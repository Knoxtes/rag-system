# rag_system.py - NEW "Agent" Architecture (Optimized)

import google.generativeai as genai
# --- ✅ CORRECTED: Import Part from protos, not types ---
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.protos import Part, FunctionResponse
import google.generativeai.types as genai_types # Use this for Schema/Tool

# Import Vertex AI for Google Cloud credits
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
    from vertexai.generative_models import Part as VertexPart
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("⚠️  Vertex AI not installed. Install with: pip install google-cloud-aiplatform")

from embeddings import LocalEmbedder, LocalReranker, HybridSearcher
from vector_store import VectorStore
from answer_logger import AnswerLogger
from config import (
    TOP_K_RESULTS, GOOGLE_API_KEY, MAX_CONTEXT_CHARACTERS, 
    INDEXED_FOLDERS_FILE, MAX_AGENT_ITERATIONS, AGENT_TEMPERATURE,
    INITIAL_RETRIEVAL_COUNT, DIVERSITY_THRESHOLD, USE_HYBRID_SEARCH,
    BM25_WEIGHT, DENSE_WEIGHT, USE_CONTEXTUAL_COMPRESSION, MAX_CHUNKS_PER_FILE,
    ENABLE_MULTI_QUERY, ENABLE_CROSS_ENCODER_FUSION, SYNTHESIS_CONTEXT_WINDOW,
    MIN_SOURCES_FOR_SYNTHESIS, ENABLE_QUERY_CACHE, CACHE_TTL_SECONDS, CACHE_MAX_SIZE,
    SYNTHESIS_QUERY_THRESHOLD, ENABLE_AI_ROUTING, AI_ROUTING_CONFIDENCE_THRESHOLD,
    PROJECT_ID, LOCATION, USE_VERTEX_AI, USE_VERTEX_EMBEDDINGS
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
import sys

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        # Try to set UTF-8 encoding for stdout
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

def safe_print(*args, **kwargs):
    """Safe print function that handles Unicode encoding errors on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace problematic Unicode characters
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common emoji with ASCII equivalents
                safe_arg = (arg.replace('👤', '[USER]')
                             .replace('🤖', '[AI]')
                             .replace('🔍', '[SEARCH]')
                             .replace('📊', '[STATS]')
                             .replace('⚡', '[FAST]')
                             .replace('💡', '[INFO]')
                             .replace('🎯', '[TARGET]')
                             .replace('📚', '[DOCS]')
                             .replace('🧠', '[AI]')
                             .replace('👁', '[VIEW]')
                             .replace('🔧', '[TOOL]')
                             .replace('⏰', '[TIME]'))
                safe_args.append(safe_arg)
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)

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

**BUSINESS PROCESS & ACTION-ORIENTED RESPONSES:**
The documents have been AI-enhanced to provide clear, actionable business processes. When users ask about procedures, workflows, or "what are the next steps":
- **Identify the specific business process** mentioned (onboarding, project management, brand development, etc.)
- **Present steps in order** with clear numbering and descriptions
- **Provide actionable guidance** - each step should tell the user exactly what to do
- **Include relevant context** like timelines, responsible parties, or prerequisites
- **For client/project queries**: Focus on practical next steps, deliverables, and stakeholder actions
- **Example response format**: "For client onboarding, here are the next steps: 1. [Action] - [Description] 2. [Action] - [Description]"

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
* `rag_search` returns: `[{"source_path": "...", "snippet": "...", "relevance": -2.15, "file_info": {"file_name": "...", "file_type": "...", "google_drive_link": "..."}}, ...]`
  - Lower (more negative) scores = less relevant, but still potentially useful
  - The snippets are already ranked best-first
  - For synthesis queries: You may receive 20-30 results from 5-10+ files - USE THEM ALL
  - **IMPORTANT**: Each result includes "file_info" with a "google_drive_link" - ALWAYS include relevant links in your response
* `search_folder` returns: Same format but filtered to specific folder
* `live_drive_search` returns: `[{"file_name": "...", "link": "..."}, ...]`

**CRITICAL: Always Include Source Links in Your Response**
- When referencing information from documents, **ALWAYS include the Google Drive link**
- Format links as: "Source: [filename](google_drive_link)" 
- For multiple sources, list each with its link
- Example: "According to the Q1 report, sales increased 15%. Source: [Q1_Sales_Report.pdf](https://docs.google.com/document/d/abc123/edit)"
- This allows users to immediately access and verify the source documents
- Make links clickable by using proper markdown format: [text](url)

**Remember:** The search is smart - it auto-expands queries AND generates multiple variations for synthesis tasks. Keep queries focused and specific. Read ALL snippets before answering, and ALWAYS include source links for referenced information!
"""

def _get_generative_model(model_name=None):
    """
    Get a generative model (Vertex AI or consumer API based on config).
    
    Args:
        model_name: Model identifier (defaults to GEMINI_MODEL from config)
    
    Returns:
        Model instance (either Vertex AI or genai)
    """
    # Use configured model if not specified
    if model_name is None:
        from config import GEMINI_MODEL
        model_name = GEMINI_MODEL
    
    if USE_VERTEX_AI:
        if not VERTEX_AI_AVAILABLE:
            print("⚠️  Vertex AI not available, falling back to consumer API")
            genai.configure(api_key=GOOGLE_API_KEY)
            return genai.GenerativeModel(model_name)
        
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print(f"  ☁️  Using Vertex AI with Google Cloud project: {PROJECT_ID}")
        
        # Map consumer model names to Vertex AI model names
        vertex_model_map = {
            'gemini-2.5-flash': 'gemini-2.5-flash',  # Flash 2.5 (cheapest)
            'gemini-2.0-flash-exp': 'gemini-2.0-flash-exp',
            'gemini-1.5-flash': 'gemini-1.5-flash',
            'gemini-1.5-pro': 'gemini-1.5-pro'
        }
        
        vertex_model_name = vertex_model_map.get(model_name, 'gemini-2.5-flash')
        print(f"  📦 Using Vertex AI model: {vertex_model_name}")
        return VertexGenerativeModel(vertex_model_name)
    else:
        # Use consumer API
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel(model_name)


class MultiCollectionRAGSystem:
    """
    Multi-Collection RAG System that can search across all available collections
    """
    
    def __init__(self, drive_service, available_collections, api_key=GOOGLE_API_KEY):
        """
        Initialize the multi-collection RAG system.
        """
        print(f"Initializing Multi-Collection RAG Agent for {len(available_collections)} collections...")
        
        self.drive_service = drive_service
        self.collection_name = "ALL_COLLECTIONS"
        self.available_collections = available_collections
        self.collection_systems = {}
        
        # Configure authentication based on USE_VERTEX_AI setting
        if USE_VERTEX_AI:
            # Vertex AI uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            print("  🌐 Using Vertex AI authentication (GOOGLE_APPLICATION_CREDENTIALS)")
        else:
            # Consumer API requires GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set! Either set GOOGLE_API_KEY or use Vertex AI (set USE_VERTEX_AI=True)")
            genai.configure(api_key=api_key)
        
        # Initialize AI model for collection routing
        self.routing_model = _get_generative_model('gemini-2.0-flash-exp')
        
        # Initialize individual RAG systems for each collection
        for collection_name, collection_info in available_collections.items():
            print(f"  → Loading collection: {collection_info['name']}")
            try:
                self.collection_systems[collection_name] = EnhancedRAGSystem(
                    drive_service, collection_name, api_key
                )
            except Exception as e:
                print(f"  ⚠️  Failed to load collection {collection_name}: {e}")
        
        print(f"[+] Multi-Collection Agent Ready! {len(self.collection_systems)} collections active.")
    
    def _route_to_best_collection(self, question: str):
        """
        Use AI to determine which collection is most likely to answer the question.
        Returns the collection_name and confidence score.
        """
        try:
            # Build collection descriptions
            collection_descriptions = []
            for coll_id, coll_info in self.available_collections.items():
                collection_descriptions.append(f"- {coll_info['name']}: {coll_info['location']} ({coll_info.get('files_processed', 0)} files)")
            
            collections_text = "\n".join(collection_descriptions)
            
            prompt = f"""Given this user question, determine which document collection is MOST LIKELY to contain the answer.

User Question: "{question}"

Available Collections:
{collections_text}

Analyze the question and respond with ONLY a JSON object in this format:
{{
  "best_collection": "exact collection name from the list above",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Consider:
- Keywords and topic (e.g., "employee", "policy", "handbook" → HR/employee documents)
- Question type (policy questions → handbooks, technical → documentation, sales → business docs)
- Be specific - if unsure, use low confidence

Respond ONLY with the JSON object, no other text."""

            response = self.routing_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            routing_result = json.loads(response_text)
            
            # Find the matching collection ID
            best_collection_name = routing_result.get('best_collection', '')
            confidence = float(routing_result.get('confidence', 0))
            reasoning = routing_result.get('reasoning', '')
            
            # Match collection name to ID
            matched_id = None
            for coll_id, coll_info in self.available_collections.items():
                if coll_info['name'].lower() == best_collection_name.lower():
                    matched_id = coll_id
                    break
            
            if matched_id and confidence > AI_ROUTING_CONFIDENCE_THRESHOLD:  # Use config threshold
                print(f"\n  🎯 AI Routing: {best_collection_name} (confidence: {confidence:.0%})")
                print(f"     Reasoning: {reasoning}")
                return matched_id, confidence
            else:
                print(f"\n  🔀 AI Routing: Low confidence ({confidence:.0%}) - searching all collections")
                return None, confidence
                
        except Exception as e:
            print(f"\n  ⚠️  Collection routing failed: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0
    
    def process_question(self, question: str, file_id=None):
        """
        Process a question across all collections and combine results
        
        Args:
            question: The user's question
            file_id: Optional file ID to filter results to a specific file
        """
        print(f"\n🔍 Multi-Collection Search: '{question[:50]}...'")
        
        if file_id:
            print(f"  📄 Filtering to specific file: {file_id}")
        
        # Step 1: Use AI to route to best collection (if enabled)
        best_collection_id = None
        routing_confidence = 0.0
        
        if ENABLE_AI_ROUTING:
            best_collection_id, routing_confidence = self._route_to_best_collection(question)
        else:
            print(f"  ℹ️  AI routing disabled (set ENABLE_AI_ROUTING=True in config.py to enable)")
        
        # Enhance query for better semantic matching
        # Add context keywords to help distinguish different types of information
        enhanced_question = question
        
        # Detect query intent and add context - be more aggressive with detection
        question_lower = question.lower()
        if any(word in question_lower for word in ['holiday', 'holidays', 'pto', 'vacation', 'time off', 'leave', 'day off', 'days off']):
            # HR/policy query - ALWAYS enhance for holidays/PTO questions
            enhanced_question = f"{question} employee policy handbook HR benefits time off leave vacation"
            print(f"  🎯 Detected HR policy query (time off/holidays), enhanced search")
        elif any(word in question_lower for word in ['benefit', 'benefits', 'insurance', 'healthcare', 'health care', 'dental', 'vision', '401k', 'retirement']):
            enhanced_question = f"{question} employee benefits policy handbook HR compensation"
            print(f"  🎯 Detected benefits query, enhanced search")
        elif any(word in question_lower for word in ['procedure', 'process', 'how to', 'steps to', 'guideline', 'guidelines']):
            enhanced_question = f"{question} procedure process guidelines documentation handbook"
            print(f"  🎯 Detected procedure query, enhanced search")
        
        all_results = []
        collection_results = {}
        
        # Search each collection (prioritize routed collection if confident)
        search_order = list(self.collection_systems.keys())
        if best_collection_id and routing_confidence > AI_ROUTING_CONFIDENCE_THRESHOLD:
            # Move best collection to front for priority search
            if best_collection_id in search_order:
                search_order.remove(best_collection_id)
                search_order.insert(0, best_collection_id)
        
        for collection_name in search_order:
            rag_system = self.collection_systems[collection_name]
            try:
                is_primary = (collection_name == best_collection_id and routing_confidence > AI_ROUTING_CONFIDENCE_THRESHOLD)
                print(f"  → Searching {self.available_collections[collection_name]['name']}{'  [PRIMARY TARGET 🎯]' if is_primary else ''}...")
                
                # Get more results from primary collection
                top_k = 12 if is_primary else 6
                
                # Use the existing search_documents function with enhanced query
                results = rag_system.search_documents(enhanced_question, top_k=top_k, file_id=file_id)
                
                if results:
                    # Tag results with collection info - don't boost yet, reranking will reset scores
                    for result in results:
                        result['collection_name'] = collection_name
                        result['collection_display'] = self.available_collections[collection_name]['name']
                        result['collection_location'] = self.available_collections[collection_name]['location']
                        result['is_primary_collection'] = is_primary  # Tag for later boosting
                    
                    all_results.extend(results)
                    collection_results[collection_name] = len(results)
                    print(f"    ✓ Found {len(results)} results")
                else:
                    collection_results[collection_name] = 0
                    print(f"    - No results")
                    
            except Exception as e:
                print(f"    ⚠️  Error searching {collection_name}: {e}")
                collection_results[collection_name] = 0
        
        if not all_results:
            print("  No results found across any collection")
            summary_info = {
                'total_results': 0,
                'collections_searched': len(self.collection_systems),
                'collection_breakdown': collection_results,
                'top_collections': []
            }
            return [], summary_info
        
        # Re-rank all results together using the first collection's reranker
        if len(self.collection_systems) > 0:
            first_system = next(iter(self.collection_systems.values()))
            
            # Prepare content for reranking
            contents = []
            for result in all_results:
                content = f"{result.get('title', '')} {result.get('content', '')}"
                contents.append(content)
            
            try:
                # Re-rank across all collections using ORIGINAL question (not enhanced)
                # Enhanced query helps retrieval but confuses reranking
                reranked_scores = first_system.reranker.rerank(question, contents)
                print(f"  🔄 Reranked {len(contents)} results using original query")
                
                # Apply new scores - handle dict or float format
                for i, result in enumerate(all_results):
                    if i < len(reranked_scores):
                        score_item = reranked_scores[i]
                        # Handle both dict and float formats
                        if isinstance(score_item, dict):
                            result['score'] = float(score_item.get('score', score_item.get('relevance_score', 0)))
                        else:
                            result['score'] = float(score_item)
                        result['rerank_score'] = result['score']  # Store original rerank score for debugging
                
                # Sort by new scores - use safe key function
                all_results.sort(key=lambda x: float(x.get('score', 0)) if isinstance(x.get('score', 0), (int, float, str)) else 0, reverse=True)
                
                # Log initial score range
                if all_results:
                    min_score = min(float(r.get('score', 0)) for r in all_results)
                    max_score = max(float(r.get('score', 0)) for r in all_results)
                    score_range = max_score - min_score
                    print(f"\n  📊 Score range before boosting: {min_score:.2f} to {max_score:.2f} (range: {score_range:.2f})")
                
                # Apply ADDITIVE boosting (not multiplicative) - works correctly with negative scores
                print(f"\n  📚 Applying smart boosting...")
                for result in all_results:
                    title = result.get('title', '').lower()
                    metadata = result.get('metadata', {})
                    file_path = metadata.get('source', '').lower()
                    original_score = float(result.get('score', 0))
                    
                    # Additive boosts - add fixed amounts instead of multiplying
                    boost_amount = 0
                    boost_reasons = []
                    
                    # Layer 1: Primary collection boost (from AI routing)
                    if result.get('is_primary_collection', False):
                        boost_amount += 2.0  # Add +2.0 to score
                        boost_reasons.append("primary collection (+2.0)")
                    
                    # Layer 2: Policy/handbook document boost (strong boost for HR documents)
                    if any(keyword in title or keyword in file_path for keyword in 
                           ['handbook', 'policy', 'policies', 'hr', 'human resource', 'employee', 'benefits', 'manual', 'guide']):
                        boost_amount += 8.0  # Add +8.0 to score (massive boost to overcome bad rerank scores)
                        boost_reasons.append("policy document (+8.0)")
                    
                    if boost_amount > 0:
                        result['score'] = original_score + boost_amount
                        boost_desc = ", ".join(boost_reasons)
                        print(f"    🔼 {title[:40]}... ({boost_desc}): {original_score:.2f} → {result['score']:.2f}")
                
                # Re-sort after boosting
                all_results.sort(key=lambda x: float(x.get('score', 0)) if isinstance(x.get('score', 0), (int, float, str)) else 0, reverse=True)
                
            except Exception as e:
                print(f"  ⚠️  Reranking failed, using original scores: {e}")
                import traceback
                traceback.print_exc()
                # Try to normalize existing scores before sorting
                for result in all_results:
                    try:
                        score = result.get('score', 0)
                        if isinstance(score, str):
                            result['score'] = float(score)
                        elif not isinstance(score, (int, float)):
                            result['score'] = 0.0
                    except (ValueError, TypeError):
                        result['score'] = 0.0
        
        # Smart filtering: Remove extremely low scoring results while keeping reasonable diversity
        # Cross-encoder scores can be negative, so we filter relative to the top score
        if all_results:
            # Sort by score first to get proper top score
            all_results_sorted = sorted(all_results, key=lambda x: float(x.get('score', -999)) if isinstance(x.get('score', 0), (int, float)) else -999, reverse=True)
            
            top_score = float(all_results_sorted[0].get('score', -999)) if all_results_sorted else -999
            # Keep results within reasonable range of top score - more aggressive filtering
            score_threshold = top_score - 2.0  # Keep results within 2 points of top score (tightened from 3)
            
            print(f"\n  📊 Top 5 results before filtering:")
            for i, r in enumerate(all_results_sorted[:5]):
                score = r.get('score', 0)
                title = r.get('title', 'Untitled')[:40]
                coll = r.get('collection_display', 'Unknown')
                print(f"     {i+1}. [{coll}] {title}... (score: {score:.2f})")
            
            filtered_results = [r for r in all_results_sorted if float(r.get('score', -999)) >= score_threshold]
            
            # Ensure we have at least 5 results even if filtering is aggressive
            if len(filtered_results) < 5:
                filtered_results = all_results_sorted[:8]
            
            print(f"\n  📏 Score threshold: {score_threshold:.2f} (top: {top_score:.2f}) - keeping {len(filtered_results)}/{len(all_results_sorted)} results")
        else:
            filtered_results = []
        
        # Ensure collection diversity - don't return all results from just one collection
        collection_counts = {}
        diverse_results = []
        MAX_PER_COLLECTION = 5  # Max results from any single collection
        
        for result in filtered_results:
            coll = result.get('collection_name', 'unknown')
            if coll not in collection_counts:
                collection_counts[coll] = 0
            
            if collection_counts[coll] < MAX_PER_COLLECTION:
                diverse_results.append(result)
                collection_counts[coll] += 1
        
        # Take top results after diversity filtering
        MAX_SOURCES = 6  # Reduced for more focused, high-quality answers
        final_results = diverse_results[:MAX_SOURCES]
        
        print(f"\n  ✅ Final {len(final_results)} sources selected:")
        for i, r in enumerate(final_results):
            title = r.get('title', 'Untitled')[:50]
            coll = r.get('collection_display', 'Unknown')[:30]
            score = r.get('score', 0)
            print(f"     {i+1}. [{coll}] {title}... (score: {score:.2f})")
        
        # Add summary info
        summary_info = {
            'total_results': len(all_results),
            'collections_searched': len(self.collection_systems),
            'collection_breakdown': collection_results,
            'top_collections': sorted(collection_results.items(), key=lambda x: x[1], reverse=True)[:3],
            'min_score': min([float(r.get('score', 0)) for r in final_results if isinstance(r.get('score', 0), (int, float))]) if final_results else 0,
            'max_score': max([float(r.get('score', 0)) for r in final_results if isinstance(r.get('score', 0), (int, float))]) if final_results else 0
        }
        
        print(f"  ✓ Combined {len(all_results)} results from {len(self.collection_systems)} collections")
        print(f"  📋 After filtering & diversity: {len(final_results)} results from {len(collection_counts)} collections")
        print(f"  → Scores: {summary_info['min_score']:.2f} to {summary_info['max_score']:.2f}")
        for coll, count in collection_counts.items():
            print(f"     • {self.available_collections.get(coll, {}).get('name', coll)}: {count} results")
        
        return final_results, summary_info
    
    def process_chat(self, question: str, file_id=None):
        """
        Process a chat question using multi-collection search and Gemini
        
        Args:
            question: The user's question
            file_id: Optional file ID to filter results to a specific file
        """
        start_time = time.time()
        
        try:
            # Search across all collections
            search_results, summary_info = self.process_question(question, file_id=file_id)
            
            if not search_results:
                return {
                    'answer': "I couldn't find any relevant information across your document collections. Please try rephrasing your question or check if the content you're looking for has been indexed.",
                    'sources': [],
                    'search_time': time.time() - start_time,
                    'multi_collection_summary': summary_info
                }
            
            # Use the first collection's system for Gemini processing
            first_system = next(iter(self.collection_systems.values()))
            
            # Build context from multi-collection results
            # CSVs/spreadsheets are now stored as complete single chunks (no multi-chunk loading needed)
            context_parts = []
            sources = []
            
            for i, result in enumerate(search_results):
                snippet = result.get('content', '')
                title = result.get('title', 'Untitled')
                collection_name = result.get('collection_display', 'Unknown Collection')
                metadata = result.get('metadata', {})
                
                # Check if this is a CSV/Excel file
                file_type = metadata.get('file_info', {}).get('mimeType', '').lower()
                is_spreadsheet = any(x in file_type for x in ['csv', 'spreadsheet', 'excel', 'sheet'])
                is_csv_filename = title.lower().endswith(('.csv', '.xlsx', '.xls'))
                
                # Note: With updated indexing, CSVs are stored as complete single chunks
                # If content has "COMPLETE FILE" marker, we know it's the full document
                is_complete_file = 'COMPLETE FILE' in snippet[:300] if snippet else False
                
                if (is_spreadsheet or is_csv_filename) and is_complete_file:
                    print(f"  📊 Spreadsheet: {title} (complete file, single chunk)")
                
                # Regular handling - CSVs are now complete in single chunks
                # Check if this is a chunk (partial document)
                chunk_info = metadata.get('chunk_info', {})
                is_chunk = chunk_info.get('chunk_index') is not None
                
                chunk_note = ""
                if is_chunk:
                    chunk_idx = chunk_info.get('chunk_index', 0)
                    total_chunks = chunk_info.get('total_chunks', 1)
                    chunk_note = f"\n[NOTE: This is chunk {chunk_idx + 1} of {total_chunks} from this document - data may be incomplete]"
                
                context_parts.append(f"""
[Source: "{title}" from {collection_name}]{chunk_note}
Content: {snippet}
""")
                
                sources.append({
                    'title': title,
                    'content': snippet[:200] + "..." if len(snippet) > 200 else snippet,
                    'score': result.get('score', 0),
                    'collection': collection_name,
                    'collection_location': result.get('collection_location', ''),
                    'url': result.get('url', ''),
                    'metadata': result.get('metadata', {})
                })
            
            context = "\n".join(context_parts)
            
            # Create enhanced prompt for multi-collection
            prompt = f"""
Based on the information from multiple document collections below, please provide a comprehensive answer to the user's question.

**User Question:** {question}

**Available Information from Collections:**
{context}

**Instructions:**
- Carefully review ALL sources provided above, especially those from employee handbooks, HR policies, or official company documents
- Synthesize information from all relevant sources across collections
- **IMPORTANT**: If the question is about company policies, benefits, or procedures, PRIORITIZE information from handbooks and policy documents over sales materials or marketing content
- **CRITICAL FOR DATA/NUMBERS**: When analyzing spreadsheets, CSV files, or numerical data:
  * Do NOT assume patterns - read ALL provided data thoroughly
  * Do NOT stop reading when you see repeated zeros or empty values
  * Do NOT extrapolate or assume remaining data follows a pattern
  * Calculate totals by summing ALL values provided, not just the first few
  * If the data appears incomplete, state that you can only report what's provided
- **CRITICAL CITATION RULE**: When citing sources, use the EXACT document title from the source headers above in the format [Source: "Document Title"]
- **ONLY include sources in your final answer that you ACTUALLY REFERENCE** - do not list unused sources
- If you reference information from a source multiple times, only cite it once with [Source: "Document Title"]
- If you find relevant information in the sources, USE IT in your answer - do not say "no information available" when sources exist
- If information conflicts between sources, prioritize official policy documents over other materials
- Provide a direct, comprehensive answer based on the sources provided

**Multi-Collection Search Summary:**
- Searched {summary_info['collections_searched']} collections
- Found {summary_info['total_results']} results, showing top {len(search_results)}
- Relevance scores: {summary_info['min_score']:.2f} to {summary_info['max_score']:.2f}
- Top contributing collections: {', '.join([f"{info[0]} ({info[1]} results)" for info in summary_info['top_collections']])}

Please provide your answer:
"""
            
            # Generate response using first system's model
            model = _get_generative_model('gemini-2.5-flash-preview-09-2025')
            response = model.generate_content(prompt)
            
            answer_text = response.text
            
            # Filter sources to only include those actually cited in the answer
            cited_sources = []
            seen_titles = set()  # Track unique titles
            
            for source in sources:
                title = source['title']
                # Check if this source is cited in the answer (case-insensitive)
                if f'"{title}"' in answer_text or title.lower() in answer_text.lower():
                    # Only add if we haven't seen this title before
                    if title not in seen_titles:
                        cited_sources.append(source)
                        seen_titles.add(title)
            
            print(f"\n  📄 Filtered sources: {len(cited_sources)}/{len(sources)} actually cited")
            
            return {
                'answer': answer_text,
                'sources': cited_sources,  # Only return cited sources
                'search_time': time.time() - start_time,
                'multi_collection_summary': summary_info
            }
            
        except Exception as e:
            print(f"Error in multi-collection chat: {e}")
            traceback.print_exc()
            return {
                'answer': f"I encountered an error while searching across collections: {str(e)}",
                'sources': [],
                'search_time': time.time() - start_time,
                'error': str(e)
            }


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
        
        # Configure authentication based on USE_VERTEX_AI setting
        if USE_VERTEX_AI:
            # Vertex AI uses GOOGLE_APPLICATION_CREDENTIALS environment variable
            # No need for api_key, authentication handled by google-auth library
            print("  🌐 Using Vertex AI authentication (GOOGLE_APPLICATION_CREDENTIALS)")
        else:
            # Consumer API requires GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set! Either set GOOGLE_API_KEY or use Vertex AI (set USE_VERTEX_AI=True)")
            genai.configure(api_key=api_key)
        
        # Load embeddings based on config
        print("Loading embeddings...")
        if USE_VERTEX_EMBEDDINGS:
            from vertex_embeddings import VertexEmbedder, VertexReranker
            print("  🌐 Using Vertex AI Embeddings (production-grade)")
            self.embedder = VertexEmbedder()
            print("Loading re-ranking model...")
            self.reranker = VertexReranker(self.embedder)
        else:
            print("  💻 Using Local Embeddings (development mode)")
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
        
        # Initialize answer logger for Q&A tracking
        print("Initializing answer logger...")
        self.answer_logger = AnswerLogger()
        
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
        print(f"[+] Agent Ready! {stats['total_documents']} documents indexed.\n")

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
            print(f"[+] Model initialization successful! Using: {model_name}")
            return model
            
        except Exception as e:
            print(f"  [!] {model_name} failed to initialize: {e}")
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
            safe_print(f"  🔍 Query analysis: {status} (confidence: {confidence:.2f}, indicators: {', '.join(matched_indicators[:3])})")
        
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
        safe_print(f"  🤖 Agent Action: rag_search(query=\"{query}\")")
        
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
            # Apply file_id filter if specified for targeted queries
            where_filter = None
            if hasattr(self, '_target_file_id') and self._target_file_id:
                where_filter = {"file_id": self._target_file_id}
                safe_print(f"  🎯 Filtering to specific file: {self._target_file_id}")
            
            results = self.vector_store.search(query_embedding, n_results=INITIAL_RETRIEVAL_COUNT, where=where_filter)
            
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
        
        safe_print(f"  📊 Multi-query search: {len(all_contexts)} unique documents retrieved")
        
        # 4.5. CSV AUTO-FETCH: If any CSV chunks are found, fetch ALL chunks from those CSV files
        # This ensures complete data for CSVs that were chunked to fit embedding model limits
        csv_files_found = {}
        for metadata in all_metadatas:
            if metadata.get('is_csv', False):
                file_id = metadata.get('file_id')
                if file_id and file_id not in csv_files_found:
                    csv_files_found[file_id] = {
                        'file_name': metadata.get('file_name'),
                        'file_path': metadata.get('file_path', ''),
                        'total_chunks': metadata.get('total_chunks', 1)
                    }
        
        if csv_files_found:
            print(f"  📊 CSV AUTO-FETCH: Found {len(csv_files_found)} CSV file(s) in search results")
            print(f"     Fetching ALL chunks to ensure complete data...")
            
            initial_doc_count = len(all_contexts)
            chunks_added = 0
            
            for file_id, info in csv_files_found.items():
                file_display = info['file_name']
                if info['file_path']:
                    file_display = f"{info['file_path']}/{info['file_name']}"
                    
                print(f"     📄 {file_display}")
                print(f"        Expected chunks: {info['total_chunks']}")
                
                # Fetch all chunks for this CSV file
                try:
                    all_docs = self.vector_store.collection.get(
                        where={"file_id": file_id}
                    )
                    
                    if all_docs and all_docs.get('documents'):
                        chunks_retrieved = len(all_docs['documents'])
                        chunks_added_for_file = 0
                        
                        for doc, metadata in zip(all_docs['documents'], all_docs['metadatas']):
                            if doc not in all_contexts:
                                all_contexts.append(doc)
                                all_metadatas.append(metadata)
                                chunks_added_for_file += 1
                        
                        chunks_added += chunks_added_for_file
                        print(f"        ✓ Retrieved: {chunks_retrieved} chunks")
                        print(f"        ✓ Added to context: {chunks_added_for_file} new chunks")
                        
                        # Warning if chunk count doesn't match expected
                        if chunks_retrieved != info['total_chunks']:
                            print(f"        ⚠️  Warning: Expected {info['total_chunks']} chunks but found {chunks_retrieved}")
                    else:
                        print(f"        ⚠️  No chunks found for file_id: {file_id}")
                        
                except Exception as e:
                    print(f"        ❌ Error fetching CSV chunks: {e}")
                    import traceback
                    traceback.print_exc()
            
            final_doc_count = len(all_contexts)
            print(f"  📊 CSV auto-fetch complete:")
            print(f"     Before: {initial_doc_count} documents")
            print(f"     After: {final_doc_count} documents (+{chunks_added} CSV chunks)")
        else:
            # Debug: Show if any documents were marked as CSV
            csv_metadata_count = sum(1 for m in all_metadatas if 'is_csv' in m)
            if csv_metadata_count == 0:
                print(f"  ℹ️  No CSV files detected in search results (no is_csv metadata flags found)")
        
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
            # Handle case where max_bm25 is 0 (all scores are 0)
            if max_bm25 == 0:
                max_bm25 = 1.0
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
                # Handle case where max_dist is 0 (all distances are 0)
                if max_dist == 0:
                    max_dist = 1.0
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
        
        safe_print(f"  📊 Final: {len(reranked_results)} documents reranked")
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
            
            # Enhanced snippet with context markers and file information
            chunk_idx = metadata.get('chunk_index', 0)
            total_chunks = metadata.get('total_chunks', 1)
            
            # Format file information with Google Drive link
            file_info = self._format_file_info(metadata)
            
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
                "relevance": score,  # Store as float, not string
                "chunk_index": chunk_idx,
                "file_info": file_info  # Enhanced with Google Drive link and metadata
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
        safe_print(f"  🤖 Agent Action: search_folder(folder=\"{folder_pattern}\", query=\"{query}\")")
        
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
            safe_print(f"  🔍 Searching within folder for: \"{expanded_query}\"")
            
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
                
                # Format file information with Google Drive link
                file_info = self._format_file_info(metadata)
                
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
                    "relevance": f"{item['score']:.2f}",
                    "file_info": file_info  # Enhanced with Google Drive link and metadata
                })
            
            print(f"  ✅ Returning {len(output_snippets)} relevant results from folder")
            return json.dumps(output_snippets)
        
        else:
            # No query - return overview of all files in folder
            safe_print(f"  📊 Returning overview of all files in folder")
            
            # Group by file
            files_in_folder = {}
            for metadata in matching_metadatas:
                file_name = metadata.get('file_name', 'unknown')
                if file_name not in files_in_folder:
                    # Format file information with Google Drive link
                    file_info = self._format_file_info(metadata)
                    
                    files_in_folder[file_name] = {
                        "file_name": file_name,
                        "file_path": f"{metadata.get('file_path', '')}{file_name}",
                        "folder": metadata.get('folder_name', ''),
                        "mime_type": metadata.get('mime_type', ''),
                        "chunks": metadata.get('total_chunks', 1),
                        "file_info": file_info  # Enhanced with Google Drive link and metadata
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
        safe_print(f"  🤖 Agent Action: live_drive_search(search_term=\"{search_term}\")")
        
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
    
    def search_documents(self, question, top_k=10, file_id=None):
        """
        Search for relevant documents and return structured results.
        This method is used by MultiCollectionRAGSystem.
        
        Args:
            question: The search query
            top_k: Number of top results to return
            file_id: Optional file ID to filter results
            
        Returns:
            List of dicts with keys: title, content, url, score
        """
        # Store file_id for tool calls
        self._target_file_id = file_id
        try:
            # Use the RAG search tool to get documents
            context_json = self._tool_rag_search(question)
            
            # Parse the JSON - _tool_rag_search returns a list of snippets directly
            snippets = json.loads(context_json)
            
            # Handle error response (dict with "error" or "status" key)
            if isinstance(snippets, dict):
                if "error" in snippets:
                    print(f"  ⚠️  RAG search returned error: {snippets.get('error')}")
                    return []
                if "status" in snippets:
                    print(f"  ⚠️  RAG search status: {snippets.get('status')}")
                    return []
            
            # snippets should be a list of dicts with keys: source_path, snippet, relevance, chunk_index, file_info
            if not isinstance(snippets, list) or not snippets:
                print(f"  ⚠️  No snippets found in search results")
                return []
            
            print(f"  ✓ Found {len(snippets)} snippets from _tool_rag_search")
            
            # Convert snippets to the format expected by MultiCollectionRAGSystem
            results = []
            for snippet in snippets[:top_k]:
                # Extract file info from the file_info dict
                file_info = snippet.get('file_info', {})
                
                # Parse relevance score - should be a float from _tool_rag_search
                relevance = snippet.get('relevance', 0.0)
                try:
                    score = float(relevance)
                except (ValueError, TypeError, AttributeError):
                    score = 0.0
                
                result = {
                    'title': file_info.get('file_name', 'Untitled'),
                    'content': snippet.get('snippet', ''),
                    'url': file_info.get('google_drive_link', ''),  # Fixed: use correct key
                    'score': score,
                    'metadata': {
                        'source': snippet.get('source_path', ''),
                        'chunk_index': snippet.get('chunk_index', 0),
                        'file_info': file_info,
                        'file_type': file_info.get('file_type', 'Document'),
                        'file_id': file_info.get('file_id', '')
                    }
                }
                results.append(result)
            
            print(f"  ✓ Returning {len(results)} formatted results")
            return results
            
        except Exception as e:
            print(f"  ⚠️  Error in search_documents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def query(self, question, chat_history=[], file_id=None):
        """
        Processes a query using the agentic loop with safety limits.
        'chat_history' is now managed *internally* by the agent.
        
        Args:
            question: The user's question
            chat_history: Previous conversation history
            file_id: Optional Google Drive file ID to filter results to a specific file
        """
        # Store file_id for use in tool calls
        self._target_file_id = file_id
        if file_id:
            safe_print("=" * 80)
            safe_print(f"📄 TARGETED FILE QUERY (file_id: {file_id})")
            safe_print("=" * 80)
        
        safe_print("=" * 80)
        safe_print(f"👤 USER: {question}")
        safe_print("=" * 80)
        
        # Start timing for response tracking
        start_time = time.time()
        
        # Check cache first (for cost optimization)
        if self.query_cache and not chat_history:  # Only cache standalone queries
            cached_result = self.query_cache.get(question)
            if cached_result:
                print("  💾 Cache hit! Returning cached response (saves API call)")
                
                # Log cached response
                try:
                    response_time = time.time() - start_time
                    metadata = {
                        'query_type': 'cached',
                        'cached': True,
                        'response_time': response_time
                    }
                    self.answer_logger.log_qa_pair(question, cached_result['answer'], metadata)
                except Exception as log_error:
                    print(f"⚠️  Warning: Failed to log cached Q&A: {log_error}")
                
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
                
                safe_print(f"  🤖 Agent Thought [{iteration_count}/{MAX_ITERATIONS}]: Need to use tool `{tool_name}`")
                
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
                        time.sleep(0.5)  # Reduce delay for rate limit recovery
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
            
            # Log the Q&A pair for tracking
            try:
                metadata = {
                    'query_type': 'agent',
                    'iterations': iteration_count,
                    'cached': False,  # This is a fresh response
                    'response_time': time.time() - start_time if 'start_time' in locals() else None
                }
                self.answer_logger.log_qa_pair(question, final_answer, metadata)
            except Exception as log_error:
                print(f"⚠️  Warning: Failed to log Q&A pair: {log_error}")
            
            # Cache result if enabled and no chat history (standalone query)
            if self.query_cache and not chat_history:
                self.query_cache.set(question, result)
                print("  💾 Cached response for future use")
            
            return result
        
        except Exception as e:
            print(f"[!] Error during agent loop: {e}")
            safe_print(f"\n🔍 Error details:")
            traceback.print_exc()
            
            # Try to get chat history if available
            try:
                history = chat.history if 'chat' in locals() else []
            except:
                history = []
            
            error_message = f"An error occurred during processing: {e}\n\nPlease try rephrasing your question or ask something simpler."
            
            # Log the error for tracking
            try:
                response_time = time.time() - start_time if 'start_time' in locals() else None
                metadata = {
                    'query_type': 'agent_error',
                    'error': str(e),
                    'response_time': response_time
                }
                self.answer_logger.log_qa_pair(question, error_message, metadata)
            except Exception as log_error:
                print(f"⚠️  Warning: Failed to log error Q&A: {log_error}")
            
            return {
                'answer': error_message,
                'chat_history': history,
                'files': [], 'contexts': [], 'query_type': 'agent_error'
            }

    def query_stream(self, message, file_id=None):
        """Yields answer chunks for streaming (token or sentence level)."""
        # This is a minimal implementation for Gemini/Vertex/OpenAI APIs that support streaming.
        # If your LLM API does not support streaming, you can yield the full answer as one chunk.
        response = self.query(message, file_id=file_id)
        answer = response.get('answer', '')
        # Example: yield by sentence (for demonstration)
        import re
        for sentence in re.split(r'(?<=[.!?]) +', answer):
            if sentence.strip():
                yield sentence
        # Optionally yield sources or metadata at the end
        # yield json.dumps({'sources': response.get('sources', [])})

    def _generate_google_drive_link(self, file_id: str, mime_type: str = None) -> str:
        """
        Generate appropriate Google Drive link based on file type
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file for determining link type
            
        Returns:
            Formatted Google Drive link
        """
        if not file_id:
            return ""
        
        # Google Workspace files (open in editor)
        if mime_type:
            if 'google-apps.document' in mime_type:
                return f"https://docs.google.com/document/d/{file_id}/edit"
            elif 'google-apps.spreadsheet' in mime_type:
                return f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
            elif 'google-apps.presentation' in mime_type:
                return f"https://docs.google.com/presentation/d/{file_id}/edit"
        
        # Default: Google Drive viewer
        return f"https://drive.google.com/file/d/{file_id}/view"
    
    def _format_file_info(self, metadata: dict) -> dict:
        """
        Format file information with Google Drive link and metadata
        
        Args:
            metadata: File metadata from vector store
            
        Returns:
            Formatted file info dictionary
        """
        file_id = metadata.get('file_id', '')
        file_name = metadata.get('file_name', 'unknown')
        mime_type = metadata.get('mime_type', '')
        file_path = metadata.get('file_path', '')
        
        # Generate appropriate link
        google_drive_link = self._generate_google_drive_link(file_id, mime_type)
        
        # Determine file type for display
        file_type = "Document"
        if mime_type:
            if 'google-apps.document' in mime_type:
                file_type = "Google Doc"
            elif 'google-apps.spreadsheet' in mime_type:
                file_type = "Google Sheets"
            elif 'google-apps.presentation' in mime_type:
                file_type = "Google Slides"
            elif 'pdf' in mime_type:
                file_type = "PDF"
            elif 'image' in mime_type:
                file_type = "Image"
            elif 'word' in mime_type or 'docx' in mime_type:
                file_type = "Word Doc"
            elif 'excel' in mime_type or 'xlsx' in mime_type:
                file_type = "Excel"
            elif 'powerpoint' in mime_type or 'pptx' in mime_type:
                file_type = "PowerPoint"
        
        return {
            'file_name': file_name,
            'file_type': file_type,
            'file_path': file_path,
            'google_drive_link': google_drive_link,
            'file_id': file_id
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