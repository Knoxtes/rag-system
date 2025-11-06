# rag_system.py - NEW "Agent" Architecture (Optimized)

import google.generativeai as genai
# --- ✅ CORRECTED: Import Part from protos, not types ---
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.protos import Part, FunctionResponse
import google.generativeai.types as genai_types # Use this for Schema/Tool
from embeddings import LocalEmbedder, LocalReranker, HybridSearcher
from vector_store import VectorStore
from config import (
    TOP_K_RESULTS, GOOGLE_API_KEY, MAX_CONTEXT_CHARACTERS, 
    INDEXED_FOLDERS_FILE, MAX_AGENT_ITERATIONS, AGENT_TEMPERATURE,
    INITIAL_RETRIEVAL_COUNT, DIVERSITY_THRESHOLD, USE_HYBRID_SEARCH,
    BM25_WEIGHT, DENSE_WEIGHT, USE_CONTEXTUAL_COMPRESSION, MAX_CHUNKS_PER_FILE,
    ENABLE_MULTI_QUERY, ENABLE_CROSS_ENCODER_FUSION, SYNTHESIS_CONTEXT_WINDOW,
    MIN_SOURCES_FOR_SYNTHESIS, ENABLE_QUERY_CACHE, CACHE_TTL_SECONDS, CACHE_MAX_SIZE,
    SYNTHESIS_QUERY_THRESHOLD
)
import webbrowser
import os
import json
from auth import authenticate_google_drive
import time
import re
from difflib import SequenceMatcher
import traceback
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from functools import lru_cache
import hashlib

# Initialize rich console for beautiful output
console = Console()

# Query Cache for API cost optimization
class QueryCache:
    """Simple time-based cache for query results to reduce API calls."""
    def __init__(self, ttl_seconds=300, max_size=1000):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str):
        """Get cached result if exists and not expired."""
        key = self._hash_query(query)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]  # Remove expired entry
        return None
    
    def set(self, query: str, result):
        """Cache query result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        
        key = self._hash_query(query)
        self.cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()

# --- ✅ FINAL FIX: Combined modern dictionary syntax with correct genai_types.Tool class ---
def _define_tools():
    """Defines the functions the AI agent can call using modern, simple syntax."""
    
    return [
        genai_types.Tool( # <--- This is correct
            function_declarations=[
                {
                    "name": "rag_search",
                    "description": (
                        "Search the indexed Google Drive vector database for a specific folder. "
                        "This is the primary tool for finding data, reports, and universal truths."
                    ),
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "query": {
                                "type": "STRING",
                                "description": "The specific, detailed query to search for (e.g., 'January 2025 projects for Red market')."
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "search_folder",
                    "description": (
                        "Search for documents within a SPECIFIC FOLDER or folder pattern. "
                        "Use this when the user mentions a folder name (e.g., '2025 Projections', 'January', 'Q1 Reports'). "
                        "This filters results to only documents in that folder path."
                    ),
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "folder_pattern": {
                                "type": "STRING",
                                "description": "The folder name or path pattern to search within (e.g., '2025 Projections', 'January', 'Reports/Q1')."
                            },
                            "query": {
                                "type": "STRING",
                                "description": "What to search for within that folder (e.g., 'CSV files', 'projections', 'summary'). Leave empty to get all documents in folder."
                            }
                        },
                        "required": ["folder_pattern"]
                    }
                },
                {
                    "name": "live_drive_search",
                    "description": (
                        "Search Google Drive for files that are *not* indexed in the database. "
                        "Use this to find newly created files or to confirm file existence."
                    ),
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "search_term": {
                                "type": "STRING",
                                "description": "Keywords to search for in file names or content (e.g., 'Q3_review_final.pdf')."
                            }
                        },
                        "required": ["search_term"]
                    }
                }
            ]
        )
    ]

# --- Agent System Prompt ---
def _get_system_prompt():
    """Gets the main system instruction prompt for the agent."""
    return """You are an expert-level financial and business analyst agent. Your task is to answer the user's question by deeply analyzing and synthesizing information.

**Your Goal:** Answer the user's question accurately and completely using the MINIMUM number of tool calls.

**Your Tools:**
1.  `rag_search(query)`: Searches the indexed document database (vector store). The query is automatically expanded with synonyms.
2.  `search_folder(folder_pattern, query)`: Searches WITHIN A SPECIFIC FOLDER. Use this when user mentions folder names.
3.  `live_drive_search(search_term)`: Searches Google Drive for files not in the database.

**FOLDER-AWARE INTELLIGENCE:**
When the user mentions folder names, paths, or organizational structures:
- "2025 Projections folder" → use `search_folder("2025 Projections", "")`
- "all CSV files in January folder" → use `search_folder("January", "CSV")`
- "explain all 2025 Projects" → use `search_folder("2025 Projects", "")`
- "summaries in Q1 Reports" → use `search_folder("Q1 Reports", "summary")`

**SYNTHESIS & MULTI-DOCUMENT QUERIES:**
When asked to summarize, compare, or aggregate information across multiple documents:
- "Summarize Q1, Q2, Q3 reports" → System automatically generates multiple queries for better coverage
- "Compare Elmira and Mansfield markets" → You'll receive diverse results from BOTH sources
- "List all packages in 2025" → Results will come from multiple documents
- **IMPORTANT**: When you see results from 3+ unique source files, USE ALL OF THEM in your answer
- **DO NOT** say "I couldn't find X" if snippets contain information about X from different files
- **Synthesize across sources** - combine information, identify patterns, highlight differences
- The system provides LARGER context windows for synthesis tasks - read thoroughly

**CRITICAL RULES:**
1. **RECOGNIZE FOLDER REQUESTS** - If user mentions a folder, subfolder, or directory name, use `search_folder` first
2. **Use SPECIFIC, DESCRIPTIVE queries** - Include key terms like dates, names, categories
   - ✅ GOOD: "list of business markets 2025" or "January sales projections all regions"
   - ❌ BAD: "markets" or "how many"
3. **Stop after 5 tool calls maximum** - If you haven't found what you need, work with what you have
4. **If a search returns no results, DON'T retry with slight variations** - Try a completely different approach or answer
5. **Work with partial information** - You don't need perfect data to provide a useful answer
6. **Read ALL snippets carefully** - For synthesis queries, information is distributed across multiple sources
7. **Check unique file count** - If you get 10+ results from 5+ files, that's comprehensive coverage
8. **Synthesize, don't just list** - Combine insights, identify trends, make comparisons

**Query Strategy:**
- For folder-specific requests: ALWAYS use `search_folder` first
- For "how many" questions: Query for lists, definitions, or category names
- For summaries: Query for specific documents (reports, projections, summaries)
- For comparisons: Use ONE broad query - the system handles multi-doc retrieval automatically
- For "all X" queries: Single query with "all" or "list" keywords - don't split it up
- Always check snippet content - it often contains the direct answer

**Tool Response Format:**
* `rag_search` returns: `[{"source_path": "...", "snippet": "...", "relevance": -2.15}, ...]`
  - Lower (more negative) scores = less relevant, but still potentially useful
  - The snippets are already ranked best-first
  - For synthesis queries: You may receive 20-30 results from 5-10+ files - USE THEM ALL
* `search_folder` returns: Same format but filtered to specific folder
* `live_drive_search` returns: `[{"file_name": "...", "link": "..."}, ...]`

**Remember:** The search is smart - it auto-expands queries AND generates multiple variations for synthesis tasks. Keep queries focused and specific. Read ALL snippets before answering!
"""


class EnhancedRAGSystem:
    """
    NEW "Agent" Architecture for RAG.
    Uses Gemini's tool-calling capabilities to reason and act.
    """
    
    def __init__(self, drive_service, collection_name, api_key=GOOGLE_API_KEY):
        """
        Initialize the RAG system for a specific collection.
        """
        print(f"Initializing RAG Agent for collection: '{collection_name}'")
        
        self.drive_service = drive_service
        self.collection_name = collection_name
        
        if collection_name.startswith("folder_"):
            self.folder_id = collection_name.replace("folder_", "")
        else:
            print(f"Warning: Collection name '{collection_name}' does not follow 'folder_ID' format. Live search may not be scoped.")
            self.folder_id = None
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set!")
        
        genai.configure(api_key=api_key)
        
        print("Loading embeddings...")
        self.embedder = LocalEmbedder()
        
        print("Loading re-ranking model...")
        self.reranker = LocalReranker()
        
        print(f"Connecting to vector store: '{self.collection_name}'")
        self.vector_store = VectorStore(collection_name=self.collection_name)
        
        # Initialize hybrid searcher if enabled
        self.hybrid_searcher = None
        if USE_HYBRID_SEARCH:
            print("Initializing hybrid search (BM25 + Dense)...")
            # Will be populated on first search with corpus
            self.hybrid_searcher = HybridSearcher()
        
        # Initialize query cache for cost optimization
        self.query_cache = None
        if ENABLE_QUERY_CACHE:
            print(f"Initializing query cache (TTL: {CACHE_TTL_SECONDS}s, Max: {CACHE_MAX_SIZE} entries)...")
            self.query_cache = QueryCache(ttl_seconds=CACHE_TTL_SECONDS, max_size=CACHE_MAX_SIZE)
        
        print("Initializing Gemini Agent Model...")
        # --- MODIFIED: Passing classic tools to init ---
        self.tools = _define_tools()
        self.llm = self._initialize_model(_get_system_prompt(), self.tools)
        
        # --- MODIFIED: Define tool implementations for the router ---
        self.tool_implementations = {
            "rag_search": self._tool_rag_search,
            "search_folder": self._tool_search_folder,
            "live_drive_search": self._tool_live_drive_search,
        }
        
        stats = self.vector_store.get_stats()
        print(f"✓ Agent Ready! {stats['total_documents']} documents indexed.\n")

    # --- MODIFIED: Function now accepts classic 'tools' object ---
    def _initialize_model(self, system_instruction, tools):
        """Initialize Gemini model with system prompt and tools."""
        
        # Safety settings to reduce refusals
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Generation config to make the model more decisive
        generation_config = genai.types.GenerationConfig(
            temperature=AGENT_TEMPERATURE,  # From config - Lower = more focused
            top_p=0.8,        # Nucleus sampling
            top_k=40,         # Top-k sampling
            max_output_tokens=2048,
        )

        # --- Listing available models for diagnostics ---
        print("\n--- Listing All Available Models (for your API Key) ---")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"  - {m.name} (Display: {m.display_name})")
        except Exception as e:
            print(f"  Could not list models: {e}")
        print("--------------------------------------------------------\n")
        
        # --- MODIFIED: Using the model you confirmed is available ---
        model_name = 'models/gemini-2.5-flash-preview-09-2025' 
        
        try:
            # --- FINAL: This is the correct, modern initialization ---
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
                tools=tools, # Pass modern tool object
                safety_settings=safety_settings,
                generation_config=generation_config  # Add generation config
            )
            print(f"✓ Model initialization successful! Using: {model_name}")
            return model
            
        except Exception as e:
            print(f"  ❌ {model_name} failed to initialize: {e}")
            print("\n  >>> HINT: The model failed to initialize. This can be due to an invalid API key,")
            print("  >>> the model not being on your available list, or (most likely) an old, cached")
            print("  >>> version of this file being run by Python.")
            print("\n  >>> PLEASE TRY: Delete the '__pycache__' folder in your project and run again.")
            raise Exception("❌ Could not initialize Gemini model!")

    # --- Tool Implementations (Private) ---
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with common variations to improve recall.
        Handles business/financial terminology.
        """
        # Common expansions for business terms
        expansions = {
            r'\bmarkets?\b': 'markets regions territories areas',
            r'\bprojects?\b': 'projects initiatives campaigns programs',
            r'\breports?\b': 'reports summaries analyses documents',
            r'\bsales?\b': 'sales revenue earnings income',
            r'\bbudgets?\b': 'budgets forecasts projections estimates',
            r'\bclients?\b': 'clients customers accounts',
        }
        
        expanded = query.lower()
        for pattern, replacement in expansions.items():
            expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
        
        # If query didn't change much, just return original
        if expanded == query.lower():
            return query
        
        # Combine original + expanded for best results
        return f"{query} {expanded}"
    
    def _is_synthesis_query(self, query: str) -> bool:
        """
        Detect if query requires synthesis across multiple documents.
        Uses confidence threshold to be more selective about multi-query mode.
        """
        synthesis_indicators = {
            # Strong indicators (weight: 1.0)
            'summarize': 1.0, 'summary': 1.0, 'summaries': 1.0,
            'compare': 1.0, 'comparison': 1.0, 'versus': 1.0, 'vs': 1.0,
            'list all': 1.0, 'show all': 1.0, 'tell me about all': 1.0,
            'all reports': 1.0, 'all markets': 1.0, 'all projects': 1.0,
            
            # Moderate indicators (weight: 0.6)
            'differences': 0.6, 'similarities': 0.6,
            'across': 0.6, 'between': 0.6,
            'overview': 0.6, 'aggregate': 0.6,
            
            # Weak indicators (weight: 0.3)
            'all': 0.3, 'every': 0.3, 'each': 0.3,
        }
        
        query_lower = query.lower()
        
        # Calculate confidence score
        confidence = 0.0
        matched_indicators = []
        
        for indicator, weight in synthesis_indicators.items():
            if indicator in query_lower:
                confidence += weight
                matched_indicators.append(indicator)
        
        # Boost confidence if multiple items detected (commas, "and")
        if ',' in query or (' and ' in query_lower and len(query.split()) > 5):
            confidence += 0.4
            matched_indicators.append("multiple items")
        
        is_synthesis = confidence >= SYNTHESIS_QUERY_THRESHOLD
        
        if matched_indicators:
            status = "✓ Synthesis" if is_synthesis else "✗ Regular"
            print(f"  🔍 Query analysis: {status} (confidence: {confidence:.2f}, indicators: {', '.join(matched_indicators[:3])})")
        
        return is_synthesis
    
    def _generate_multi_queries(self, query: str) -> list:
        """
        Generate multiple query variations for better recall on synthesis tasks.
        Decomposes complex queries into simpler sub-queries.
        """
        if not ENABLE_MULTI_QUERY:
            return [query]
        
        queries = [query]  # Always include original
        query_lower = query.lower()
        
        # Pattern 1: "Summarize X, Y, and Z" → ["X summary", "Y summary", "Z summary"]
        if 'summarize' in query_lower or 'summary' in query_lower:
            # Extract list items (simple heuristic)
            if ',' in query or ' and ' in query:
                items = re.split(r',|\band\b', query, flags=re.IGNORECASE)
                for item in items:
                    item = item.strip()
                    if len(item) > 3 and 'summarize' not in item.lower():
                        queries.append(f"{item} summary overview")
        
        # Pattern 2: "Compare X and Y" → ["X details", "Y details", "X vs Y"]
        if 'compare' in query_lower or 'comparison' in query_lower:
            # Extract items being compared
            match = re.search(r'compare\s+(.+?)\s+(?:and|vs|versus)\s+(.+)', query, re.IGNORECASE)
            if match:
                item1, item2 = match.groups()
                queries.append(f"{item1.strip()} characteristics features")
                queries.append(f"{item2.strip()} characteristics features")
                queries.append(f"{item1.strip()} versus {item2.strip()} differences")
        
        # Pattern 3: "All X" → ["X list", "X examples", "X types"]
        if query_lower.startswith('all ') or ' all ' in query_lower:
            base = query.replace('all ', '').replace('All ', '')
            queries.append(f"{base} list examples")
            queries.append(f"{base} types categories")
        
        # Pattern 4: Add "overview" variation for synthesis queries
        if self._is_synthesis_query(query) and 'overview' not in query_lower:
            queries.append(f"{query} overview")
        
        # Remove duplicates and limit
        unique_queries = []
        for q in queries:
            if q not in unique_queries:
                unique_queries.append(q)
        
        return unique_queries[:4]  # Max 4 queries to avoid over-searching
    
    def _deduplicate_results(self, snippets: list) -> list:
        """
        Remove near-duplicate results to increase diversity.
        Uses text similarity to filter redundant chunks.
        """
        if len(snippets) <= 1:
            return snippets
        
        unique_snippets = []
        seen_texts = []
        
        for snippet in snippets:
            text = snippet['snippet'][:500]  # Compare first 500 chars
            is_duplicate = False
            
            # Check against already selected snippets
            for seen_text in seen_texts:
                similarity = SequenceMatcher(None, text, seen_text).ratio()
                if similarity > DIVERSITY_THRESHOLD:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_snippets.append(snippet)
                seen_texts.append(text)
        
        return unique_snippets
    
    # --- MODIFIED: Docstring updated to match 'rag_search' ---
    def _tool_rag_search(self, query: str):
        """
        [This tool is called 'rag_search' by the AI]
        Search the indexed Google Drive vector database for a specific folder.
        This is the primary tool for finding data, reports, and universal truths.
        Uses hybrid search (BM25 + dense embeddings), contextual compression,
        and multi-query for synthesis tasks.
        
        Args:
            query: The specific, detailed query to search for.
        """
        print(f"  🤖 Agent Action: rag_search(query=\"{query}\")")
        
        # Check if this is a synthesis query
        is_synthesis = self._is_synthesis_query(query)
        if is_synthesis:
            print(f"  🔬 Detected synthesis query - using multi-query strategy")
        
        # Generate multiple query variations for synthesis tasks
        queries = self._generate_multi_queries(query) if is_synthesis else [query]
        
        if len(queries) > 1:
            print(f"  📝 Generated {len(queries)} query variations for better coverage")
            for i, q in enumerate(queries, 1):
                print(f"     {i}. \"{q[:80]}...\"" if len(q) > 80 else f"     {i}. \"{q}\"")
        
        # Collect results from all query variations
        all_contexts = []
        all_metadatas = []
        all_scores = []
        
        for query_variant in queries:
            # 1. Query Expansion - Improve recall with synonyms
            expanded_query = self._expand_query(query_variant)
            
            # 2. Embed the expanded query
            query_embedding = self.embedder.embed_query(expanded_query)
            
            # 3. Vector Search (Dense Semantic Search)
            results = self.vector_store.search(query_embedding, n_results=INITIAL_RETRIEVAL_COUNT)
            
            if not results['documents'] or not results['documents'][0]:
                continue
            
            # 4. Extract contexts and metadata
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                # Avoid duplicates from multiple queries
                if doc not in all_contexts:
                    all_contexts.append(doc)
                    all_metadatas.append(metadata)
        
        if not all_contexts:
            return json.dumps({"error": "No documents found in the database."})
        
        print(f"  📊 Multi-query search: {len(all_contexts)} unique documents retrieved")
        
        # 5. HYBRID SEARCH: Combine BM25 (keyword) + Dense (semantic)
        contexts = all_contexts
        metadatas = all_metadatas
        
        if USE_HYBRID_SEARCH and self.hybrid_searcher:
            # Build/update BM25 index with current contexts
            self.hybrid_searcher.update_corpus(contexts)
            
            # Get BM25 scores
            bm25_results = self.hybrid_searcher.search(query, top_k=len(contexts))
            bm25_scores = {idx: score for idx, score in bm25_results}
            
            # Normalize scores to 0-1 range
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
            normalized_bm25 = {idx: score/max_bm25 for idx, score in bm25_scores.items()}
            
            # For multi-query, we don't have dense scores, so weight BM25 more
            if len(queries) > 1:
                # Re-sort by BM25 scores only
                sorted_indices = sorted(range(len(contexts)), key=lambda x: normalized_bm25.get(x, 0), reverse=True)
                contexts = [contexts[i] for i in sorted_indices]
                metadatas = [metadatas[i] for i in sorted_indices]
                print(f"  🔀 Multi-query mode: Using BM25 ranking")
            else:
                # Single query: use full hybrid search
                dense_scores = results.get('distances', [[]])[0]
                max_dist = max(dense_scores) if dense_scores else 1.0
                normalized_dense = {idx: 1 - (dist/max_dist) for idx, dist in enumerate(dense_scores)}
                
                # Combine scores with weights
                hybrid_scores = {}
                for idx in range(len(contexts)):
                    bm25_score = normalized_bm25.get(idx, 0)
                    dense_score = normalized_dense.get(idx, 0)
                    hybrid_scores[idx] = (BM25_WEIGHT * bm25_score) + (DENSE_WEIGHT * dense_score)
                
                sorted_indices = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)
                contexts = [contexts[i] for i in sorted_indices]
                metadatas = [metadatas[i] for i in sorted_indices]
                print(f"  🔀 Hybrid search: BM25 ({BM25_WEIGHT}) + Dense ({DENSE_WEIGHT})")
        
        # 6. Rerank with original query (not expanded) for precision
        reranked_results = self.reranker.rerank(query, contexts)
        
        print(f"  📊 Final: {len(reranked_results)} documents reranked")
        if reranked_results:
            top_score = reranked_results[0]['score']
            print(f"  📈 Top relevance score: {top_score:.3f}")
        
        # 7. For synthesis queries, return MORE results with LARGER context
        max_results = TOP_K_RESULTS
        max_context = MAX_CONTEXT_CHARACTERS
        
        if is_synthesis:
            max_results = min(TOP_K_RESULTS * 2, 30)  # Up to 30 results for synthesis
            max_context = SYNTHESIS_CONTEXT_WINDOW  # Larger context window
            print(f"  🔬 Synthesis mode: Returning up to {max_results} results with {max_context} char context")
        
        # 8. Format Output for AI (Precise Snippets)
        output_snippets = []
        file_counts = {}  # Track chunks per file for diversity
        unique_files = set()  # Track unique source files
        
        for item in reranked_results:
            score = item['score']
            context_text = item['context']
            
            # Find the original metadata
            try:
                original_index = contexts.index(context_text)
                metadata = metadatas[original_index]
            except ValueError:
                continue

            # Diversity: Limit chunks from same file
            file_name = metadata.get('file_name', 'unknown')
            if file_name not in file_counts:
                file_counts[file_name] = 0
            
            # Skip if we already have MAX_CHUNKS_PER_FILE chunks from this file
            if file_counts[file_name] >= MAX_CHUNKS_PER_FILE:
                continue
            
            file_counts[file_name] += 1
            
            full_path = f"{metadata.get('file_path', '')}{file_name}"
            
            # Enhanced snippet with context markers
            chunk_idx = metadata.get('chunk_index', 0)
            total_chunks = metadata.get('total_chunks', 1)
            
            # CONTEXTUAL COMPRESSION: Extract only relevant sentences
            snippet = context_text
            if USE_CONTEXTUAL_COMPRESSION:
                snippet = self.reranker.compress_context(query, context_text, threshold=0.3)
            
            # Truncate snippet to save tokens (use larger context for synthesis)
            snippet = snippet[:max_context]
            if len(context_text) > max_context:
                snippet += "..."
            
            # Add chunk position info for multi-chunk documents
            if total_chunks > 1:
                snippet = f"[Part {chunk_idx+1}/{total_chunks}] {snippet}"
            
            output_snippets.append({
                "source_path": full_path,
                "snippet": snippet,
                "relevance": f"{score:.2f}",
                "chunk_index": chunk_idx
            })
            
            unique_files.add(file_name)
            
            # Stop when we have enough diverse results
            if len(output_snippets) >= max_results:
                break
        
        # 9. Apply deduplication for final diversity
        unique_snippets = self._deduplicate_results(output_snippets)
        
        # 10. For synthesis queries, verify we have enough unique sources
        if is_synthesis and len(unique_files) < MIN_SOURCES_FOR_SYNTHESIS:
            print(f"  ⚠️  Warning: Only found {len(unique_files)} unique sources (minimum {MIN_SOURCES_FOR_SYNTHESIS} recommended)")
        
        print(f"  ✅ Returning {len(unique_snippets)} unique results from {len(unique_files)} files")
        
        if not unique_snippets:
            return json.dumps({"status": "No relevant documents found after filtering."})
            
        return json.dumps(unique_snippets)

    def _tool_search_folder(self, folder_pattern: str, query: str = ""):
        """
        Search for documents within a specific folder or folder pattern.
        This filters results to only show documents from the specified folder path.
        
        Args:
            folder_pattern: Folder name or path pattern (e.g., "2025 Projections", "January", "Reports/Q1")
            query: Optional search query within that folder. If empty, returns all docs in folder.
        """
        print(f"  🤖 Agent Action: search_folder(folder=\"{folder_pattern}\", query=\"{query}\")")
        
        # Get all documents from the collection with their metadata
        try:
            all_results = self.vector_store.collection.get(
                include=["metadatas", "documents"]
            )
        except Exception as e:
            return json.dumps({"error": f"Could not fetch documents: {str(e)}"})
        
        if not all_results or not all_results.get('metadatas'):
            return json.dumps({"error": "No documents found in database."})
        
        # Filter documents by folder pattern
        folder_pattern_lower = folder_pattern.lower()
        matching_docs = []
        matching_metadatas = []
        
        for doc, metadata in zip(all_results['documents'], all_results['metadatas']):
            # Check if folder pattern appears in file_path or folder_name
            file_path = metadata.get('file_path', '').lower()
            folder_name = metadata.get('folder_name', '').lower()
            
            if folder_pattern_lower in file_path or folder_pattern_lower in folder_name:
                matching_docs.append(doc)
                matching_metadatas.append(metadata)
        
        print(f"  📁 Found {len(matching_docs)} documents in folder matching '{folder_pattern}'")
        
        if not matching_docs:
            return json.dumps({
                "status": f"No documents found in folder '{folder_pattern}'.",
                "suggestion": "Try a different folder name or check the folder structure."
            })
        
        # If query is provided, search within the filtered documents
        if query and query.strip():
            # Expand query
            expanded_query = self._expand_query(query)
            print(f"  🔍 Searching within folder for: \"{expanded_query}\"")
            
            # Embed query
            query_embedding = self.embedder.embed_query(expanded_query)
            
            # Search only within the filtered documents
            # We'll rerank the filtered docs by the query
            reranked = self.reranker.rerank(query, matching_docs)
            
            # Take top results
            top_results = reranked[:min(TOP_K_RESULTS, len(reranked))]
            
            # Build output
            output_snippets = []
            for item in top_results:
                context_text = item['context']
                
                # Find original metadata
                try:
                    original_index = matching_docs.index(context_text)
                    metadata = matching_metadatas[original_index]
                except ValueError:
                    continue
                
                full_path = f"{metadata.get('file_path', '')}{metadata.get('file_name', 'unknown')}"
                chunk_idx = metadata.get('chunk_index', 0)
                total_chunks = metadata.get('total_chunks', 1)
                
                snippet = context_text[:MAX_CONTEXT_CHARACTERS]
                if len(context_text) > MAX_CONTEXT_CHARACTERS:
                    snippet += "..."
                
                if total_chunks > 1:
                    snippet = f"[Part {chunk_idx+1}/{total_chunks}] {snippet}"
                
                output_snippets.append({
                    "source_path": full_path,
                    "folder": metadata.get('folder_name', ''),
                    "snippet": snippet,
                    "relevance": f"{item['score']:.2f}"
                })
            
            print(f"  ✅ Returning {len(output_snippets)} relevant results from folder")
            return json.dumps(output_snippets)
        
        else:
            # No query - return overview of all files in folder
            print(f"  📊 Returning overview of all files in folder")
            
            # Group by file
            files_in_folder = {}
            for metadata in matching_metadatas:
                file_name = metadata.get('file_name', 'unknown')
                if file_name not in files_in_folder:
                    files_in_folder[file_name] = {
                        "file_name": file_name,
                        "file_path": f"{metadata.get('file_path', '')}{file_name}",
                        "folder": metadata.get('folder_name', ''),
                        "mime_type": metadata.get('mime_type', ''),
                        "chunks": metadata.get('total_chunks', 1)
                    }
            
            file_list = list(files_in_folder.values())
            print(f"  ✅ Found {len(file_list)} unique files in folder '{folder_pattern}'")
            
            return json.dumps({
                "folder": folder_pattern,
                "total_files": len(file_list),
                "files": file_list[:50]  # Limit to 50 files to avoid token overflow
            })

    def _tool_live_drive_search(self, search_term: str):
        """
        Search Google Drive for files that are *not* indexed in the database.
        Use this to find newly created files or to confirm file existence.
        
        Args:
            search_term: Keywords to search for in file names or content.
        """
        print(f"  🤖 Agent Action: live_drive_search(search_term=\"{search_term}\")")
        
        if self.drive_service is None:
            return json.dumps({"error": "Live search disabled."})
        
        if self.folder_id is None:
            scope_query = "trashed=false"
        else:
            # --- ✅ FIX: Corrected typo 'trasGhed' to 'trashed' ---
            scope_query = f"trashed=false and '{self.folder_id}' in parents"
        
        formatted_results = []
        try:
            safe_query = search_term.replace("'", "\\'")
            full_query = f"(name contains '{safe_query}' or fullText contains '{safe_query}') and {scope_query}"
            
            # --- MODIFIED: Restored missing API call logic ---
            response = self.drive_service.files().list(
                q=full_query, pageSize=5, fields="files(id, name, webViewLink)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            
            for file in response.get('files', []):
                formatted_results.append({
                    "file_name": file['name'],
                    "link": file['webViewLink']
                })
            
            if not formatted_results:
                return json.dumps({"status": "No new files found."})
            # --- End of restored logic ---
            
            return json.dumps(formatted_results)
            
        except Exception as e:
            return json.dumps({"error": f"Live search failed: {str(e)}"})

    # --- The NEW Agent Executor Loop ---
    
    def query(self, question, chat_history=[]):
        """
        Processes a query using the agentic loop with safety limits.
        'chat_history' is now managed *internally* by the agent.
        """
        print("=" * 80)
        print(f"👤 USER: {question}")
        print("=" * 80)
        
        # Check cache first (for cost optimization)
        if self.query_cache and not chat_history:  # Only cache standalone queries
            cached_result = self.query_cache.get(question)
            if cached_result:
                print("  💾 Cache hit! Returning cached response (saves API call)")
                return cached_result
        
        # --- Safety mechanisms ---
        MAX_ITERATIONS = MAX_AGENT_ITERATIONS  # From config
        iteration_count = 0
        query_cache = set()  # Track queries to prevent duplicates
        
        # --- MODIFIED: Use new ChatSession ---
        # We pass the *full* system prompt and tools to the model
        chat = self.llm.start_chat(
            # enable_automatic_function_calling=True, # Turn this off for manual routing
            history=chat_history # Pass previous history
        )

        try:
            # Send the user's question
            response = chat.send_message(question)
            
            # Safety check: Ensure response is valid
            if not response or not hasattr(response, 'candidates'):
                return {
                    'answer': "I received an empty response from the AI model. Please try again.",
                    'chat_history': chat.history,
                    'files': [], 'contexts': [], 'query_type': 'agent_error'
                }
            
            # --- MODIFIED: Manual ReAct Loop with safety limits ---
            # Check if response has the expected structure before accessing
            while (response.candidates and 
                   len(response.candidates) > 0 and 
                   response.candidates[0].content.parts and
                   len(response.candidates[0].content.parts) > 0 and
                   hasattr(response.candidates[0].content.parts[0], 'function_call') and
                   response.candidates[0].content.parts[0].function_call):
                
                function_call = response.candidates[0].content.parts[0].function_call
                tool_name = function_call.name
                
                # --- Safety Check 1: Max iterations ---
                iteration_count += 1
                if iteration_count > MAX_ITERATIONS:
                    print(f"\n⚠️  Maximum iterations ({MAX_ITERATIONS}) reached. Forcing final answer...")
                    # Send a message to force the agent to answer with what it has
                    force_answer_response = FunctionResponse(
                        name=tool_name,
                        response={"content": json.dumps({
                            "status": "Tool limit reached. Please provide your final answer based on the information gathered so far."
                        })}
                    )
                    response = chat.send_message(
                        Part(function_response=force_answer_response)
                    )
                    break
                
                print(f"  🤖 Agent Thought [{iteration_count}/{MAX_ITERATIONS}]: Need to use tool `{tool_name}`")
                
                if tool_name not in self.tool_implementations:
                    print(f"  ...Unknown tool: {tool_name}")
                    break

                # Call the tool function
                tool_function = self.tool_implementations[tool_name]
                # Extract arguments from the function_call.args (which is a Struct)
                tool_args = dict(function_call.args)
                
                # --- Safety Check 2: Duplicate query detection ---
                # Create a cache key from tool name and args
                cache_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
                if cache_key in query_cache:
                    print(f"  ⚠️  Duplicate query detected! Skipping and forcing progress...")
                    duplicate_response = FunctionResponse(
                        name=tool_name,
                        response={"content": json.dumps({
                            "status": "This query was already executed. Please try a different approach or provide your final answer."
                        })}
                    )
                    response = chat.send_message(
                        Part(function_response=duplicate_response)
                    )
                    continue
                
                query_cache.add(cache_key)
                
                # Run the tool
                try:
                    tool_result = tool_function(**tool_args)
                except Exception as tool_error:
                    print(f"  ✗ Tool error: {tool_error}")
                    # Handle rate limits gracefully
                    if "quota" in str(tool_error).lower() or "rate" in str(tool_error).lower():
                        print(f"  ⚠️  Rate limit hit. Waiting 2 seconds...")
                        time.sleep(2)
                        tool_result = json.dumps({"error": "Rate limit reached. Please provide answer with available information."})
                    else:
                        tool_result = json.dumps({"error": f"Tool failed: {str(tool_error)}"})
                
                # Send the result back to the model
                function_response = FunctionResponse(
                    name=tool_name,
                    response={"content": tool_result}
                )
                response = chat.send_message(
                    Part(function_response=function_response)
                )
            
            # Once the loop finishes, 'response' is the final answer
            # Safely extract the text response
            try:
                final_answer = response.text
            except Exception as text_error:
                print(f"⚠️  Warning: Could not extract response text: {text_error}")
                # Try alternative methods to get the response
                if hasattr(response, 'candidates') and response.candidates:
                    if hasattr(response.candidates[0], 'content'):
                        final_answer = str(response.candidates[0].content)
                    else:
                        final_answer = "I encountered an issue generating the response."
                else:
                    final_answer = "I encountered an issue generating the response."
            
            # --- Format and return the final response ---
            print("=" * 80)
            
            # Render markdown beautifully in console
            console.print(Panel(
                Markdown(final_answer),
                title=f"[bold cyan]💬 AI Response[/bold cyan] [dim](after {iteration_count} tool calls)[/dim]",
                border_style="cyan",
                padding=(1, 2)
            ))
            
            print("=" * 80)
            
            # We just return the text. We'll extract files if we want later.
            result = {
                'answer': final_answer,
                'chat_history': chat.history, # <-- Return the updated history
                'files': [], # File citation is now IN the text
                'contexts': [], 
                'query_type': 'agent'
            }
            
            # Cache result if enabled and no chat history (standalone query)
            if self.query_cache and not chat_history:
                self.query_cache.set(question, result)
                print("  💾 Cached response for future use")
            
            return result
        
        except Exception as e:
            print(f"❌ Error during agent loop: {e}")
            print(f"\n🔍 Error details:")
            traceback.print_exc()
            
            # Try to get chat history if available
            try:
                history = chat.history if 'chat' in locals() else []
            except:
                history = []
            
            return {
                'answer': f"An error occurred during processing: {e}\n\nPlease try rephrasing your question or ask something simpler.",
                'chat_history': history,
                'files': [], 'contexts': [], 'query_type': 'agent_error'
            }

    def open_file(self, file_id):
        """Helper to open a file (unchanged)."""
        url = f"https://drive.google.com/file/d/{file_id}/view"
        try:
            webbrowser.open(url)
        except Exception:
            print(f"Manually visit: {url}")


def load_indexed_folders():
    """Helper to load the folder log (unchanged)"""
    if os.path.exists(INDEXED_FOLDERS_FILE):
        # --- ✅ FINAL FIX: Removed the extra '.' ---
        with open(INDEXED_FOLDERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def interactive_mode(collection_name, collection_display_name):
    """
    Interactive Q&A mode for the NEW Agent.
    """
    print("\n" + "=" * 80)
    print(f"RAG AGENT - CHATTING WITH: {collection_display_name}")
    print(f"(Collection: {collection_name})")
    print("=" * 80)
    print("\nInitializing...")
    
    try:
        drive_service = authenticate_google_drive()
        rag = EnhancedRAGSystem(
            drive_service=drive_service,
            collection_name=collection_name
        )
    except Exception as e:
        print(f"\n✗ Initialization error: {e}")
        return
    
    print("\n" + "=" * 80)
    print("Ready! Ask complex, multi-step questions.")
    print("Try: 'Summarize 2025 projects for January across all markets.'")
    print("Commands: 'quit' or 'exit' to stop")
    print("=" * 80)
    print()
    
    # --- MODIFIED: Maintain chat history ---
    chat_history = [] 
    while True:
        try:
            question = input("\n💬 Your query: ").strip()
            if not question: continue
            if question.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            print()
            start_time = time.time()
            # Pass the history and get the updated one back
            result = rag.query(question, chat_history)
            chat_history = result.get('chat_history', []) # Update history
            
            end_time = time.time()
            print(f"\n(Total time: {end_time - start_time:.2f} seconds)")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    print("This file is not meant to be run directly.")
    print("Please run `python main.py` to start the system.")