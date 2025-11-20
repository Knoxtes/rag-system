# vertex_embeddings.py - Vertex AI embeddings for scalable production use

import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
import numpy as np
from typing import List, Optional
from config import PROJECT_ID, LOCATION, ENABLE_EMBEDDING_CACHE, EMBEDDING_CACHE_DIR, EMBEDDING_CACHE_TTL_DAYS
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not available, using character count approximation for token counting")


class VertexEmbedder:
    """
    Generate embeddings using Vertex AI - fully managed and scalable.
    
    Benefits over local embeddings:
    - No server CPU/GPU usage
    - Auto-scaling for concurrent requests
    - Lower latency at scale
    - Google-managed infrastructure
    - Cost: ~$0.00002 per 1K characters (~$0.30/month for 100 users)
    """
    
    def __init__(self, model_name: str = "text-embedding-004"):
        """
        Initialize Vertex AI embeddings.
        
        Supported models:
        - text-embedding-004: Latest, 768 dimensions, best quality
        - textembedding-gecko@003: 768 dimensions, balanced
        - textembedding-gecko@002: 768 dimensions, legacy
        """
        print(f"🌐 Initializing Vertex AI Embeddings: {model_name}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.model = TextEmbeddingModel.from_pretrained(model_name)
        self.model_name = model_name
        self.dimension = 768  # Vertex embeddings are 768-dimensional
        
        # Token limits for Vertex AI embedding models
        self.max_tokens = 20000  # Vertex AI embedding model limit
        self.max_batch_tokens = 18000  # Leave some buffer
        
        # Initialize tokenizer for counting tokens (approximate)
        self.tokenizer = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer as approximation
            except:
                pass
        
        print(f"  ✓ Vertex AI Embeddings ready! Dimension: {self.dimension}")
        
        # Initialize embedding cache if enabled
        self.cache = None
        if ENABLE_EMBEDDING_CACHE:
            try:
                from embedding_cache import EmbeddingCache
                self.cache = EmbeddingCache(
                    cache_dir=EMBEDDING_CACHE_DIR,
                    ttl_days=EMBEDDING_CACHE_TTL_DAYS
                )
                print(f"  ✓ Embedding cache enabled")
            except ImportError:
                print("  ⚠️  embedding_cache module not found, caching disabled")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate)"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate 1 token = 4 characters
            return len(text) // 4
    
    def split_texts_by_tokens(self, texts, max_tokens: int):
        """Split texts into batches that don't exceed token limit"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text in texts:
            text_tokens = self.count_tokens(text)
            
            # If single text exceeds limit, truncate it
            if text_tokens > max_tokens:
                if self.tokenizer:
                    # Truncate to max_tokens
                    tokens = self.tokenizer.encode(text)[:max_tokens]
                    text = self.tokenizer.decode(tokens)
                    text_tokens = max_tokens
                else:
                    # Fallback: truncate by characters
                    text = text[:max_tokens * 4]
                    text_tokens = max_tokens
                print(f"  ✂️  Truncated text from {self.count_tokens(text)} to {text_tokens} tokens")
            
            # Check if adding this text would exceed the limit
            if current_tokens + text_tokens > max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                current_batch.append(text)
                current_tokens += text_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def embed_documents(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
        """
        Generate embeddings for multiple documents.
        
        Args:
            texts: List of texts to embed
            task_type: Task type hint for the model:
                - RETRIEVAL_DOCUMENT: For documents to be retrieved
                - RETRIEVAL_QUERY: For search queries
                - SEMANTIC_SIMILARITY: For similarity comparisons
                - CLASSIFICATION: For classification tasks
                - CLUSTERING: For clustering tasks
        
        Returns:
            numpy array of embeddings (shape: [len(texts), 768])
        """
        if not texts:
            return np.array([])
        
        # Try to get from cache first
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        if self.cache:
            for i, text in enumerate(texts):
                cached = self.cache.get(text)
                if cached is not None:
                    cached_embeddings.append((i, cached))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))
        
        # Generate embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            print(f"  🌐 Generating {len(uncached_texts)} embeddings via Vertex AI...")
            
            # Split texts by token limits
            token_batches = self.split_texts_by_tokens(uncached_texts, self.max_batch_tokens)
            print(f"  📦 Split into {len(token_batches)} token-limited batches")
            
            for batch_idx, batch in enumerate(token_batches):
                # Further split by count (Vertex AI supports up to 250 texts per request)
                count_batch_size = 250
                
                for i in range(0, len(batch), count_batch_size):
                    sub_batch = batch[i:i + count_batch_size]
                    
                    # Create TextEmbeddingInput objects with task type
                    inputs = [TextEmbeddingInput(text, task_type) for text in sub_batch]
                    
                    # Get embeddings
                    embeddings = self.model.get_embeddings(inputs)
                    
                    # Extract values
                    batch_embeddings = [emb.values for emb in embeddings]
                    new_embeddings.extend(batch_embeddings)
                    
                    if len(token_batches) > 1 or len(batch) > count_batch_size:
                        print(f"    ✓ Processed batch {batch_idx + 1}/{len(token_batches)}, sub-batch {i//count_batch_size + 1}")
            
            # Cache the new embeddings
            if self.cache:
                self.cache.set_batch(uncached_texts, new_embeddings)
        
        # Combine cached and new embeddings in original order
        all_embeddings = [None] * len(texts)
        
        for i, emb in cached_embeddings:
            all_embeddings[i] = emb
        
        for i, emb in zip(uncached_indices, new_embeddings):
            all_embeddings[i] = emb
        
        # Show cache statistics
        if self.cache and len(texts) > 0:
            stats = self.cache.get_stats()
            print(f"  📊 Cache: {len(cached_embeddings)}/{len(texts)} hits ({stats['hit_rate']}, {stats['total_entries']} total)")
        
        return np.array(all_embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        Args:
            query: Search query text
        
        Returns:
            numpy array of embedding (shape: [768])
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(query)
            if cached is not None:
                return np.array(cached)
        
        # Use RETRIEVAL_QUERY task type for queries
        inputs = [TextEmbeddingInput(query, "RETRIEVAL_QUERY")]
        embeddings = self.model.get_embeddings(inputs)
        embedding = embeddings[0].values
        
        # Cache the result
        if self.cache:
            self.cache.set(query, embedding)
        
        return np.array(embedding)
    
    def get_sentence_embedding_dimension(self) -> int:
        """Return embedding dimension for compatibility with LocalEmbedder"""
        return self.dimension


# Simplified reranker using Vertex AI embeddings (no separate model needed)
class VertexReranker:
    """
    Reranks documents using cosine similarity with Vertex AI embeddings.
    Much simpler than local cross-encoder and leverages high-quality Vertex embeddings.
    """
    
    def __init__(self, embedder: Optional[VertexEmbedder] = None):
        """
        Initialize reranker.
        
        Args:
            embedder: Optional VertexEmbedder instance. If None, creates new one.
        """
        self.embedder = embedder or VertexEmbedder()
        print("  ✓ Vertex Reranker ready (using embedding similarity)")
    
    def rerank(self, query: str, contexts: list, return_scores: bool = True):
        """
        Rerank contexts using cosine similarity with embeddings
        
        Args:
            query: Search query
            contexts: List of text chunks to rerank
            return_scores: If True, include scores in results
        
        Returns:
            List of dicts with 'score' and 'context', sorted by relevance
        """
        if not contexts:
            return []
        
        # Limit contexts to prevent token overflow
        # Estimate tokens and truncate if necessary
        total_estimated_tokens = sum(self.embedder.count_tokens(ctx) for ctx in contexts)
        
        if total_estimated_tokens > self.embedder.max_batch_tokens:
            print(f"  ⚠️  Contexts too large ({total_estimated_tokens} tokens), limiting for reranking...")
            
            # Keep contexts until we hit the token limit
            limited_contexts = []
            token_count = 0
            
            for ctx in contexts:
                ctx_tokens = self.embedder.count_tokens(ctx)
                if token_count + ctx_tokens <= self.embedder.max_batch_tokens:
                    limited_contexts.append(ctx)
                    token_count += ctx_tokens
                else:
                    break
            
            contexts = limited_contexts
            print(f"  📝 Limited to {len(contexts)} contexts ({token_count} tokens)")
        
        # Handle edge cases
        if not contexts:
            return []
        
        # Get embeddings
        query_emb = self.embedder.embed_query(query)
        context_embs = self.embedder.embed_documents(contexts, task_type="RETRIEVAL_DOCUMENT")
        
        # Convert to numpy arrays and handle edge cases
        query_emb = np.array(query_emb)
        context_embs = np.array(context_embs)
        
        # Check for valid embeddings
        if context_embs.size == 0 or len(context_embs.shape) != 2:
            print(f"  ⚠️  Invalid context embeddings shape: {context_embs.shape}")
            return []
        
        # Calculate cosine similarities with safe normalization
        query_norm = np.linalg.norm(query_emb)
        if query_norm == 0:
            print(f"  ⚠️  Query embedding has zero norm")
            return []
        
        query_normalized = query_emb / query_norm
        
        # Normalize context embeddings
        context_norms = np.linalg.norm(context_embs, axis=1, keepdims=True)
        
        # Handle zero norms in context embeddings
        zero_norm_mask = context_norms.flatten() == 0
        if np.any(zero_norm_mask):
            print(f"  ⚠️  {np.sum(zero_norm_mask)} context embeddings have zero norm, skipping them")
            # Replace zero norms with 1 to avoid division by zero
            context_norms[zero_norm_mask] = 1.0
        
        context_normalized = context_embs / context_norms
        
        # Compute similarities
        similarities = np.dot(context_normalized, query_normalized)
        
        # Set zero scores for contexts that had zero norm
        similarities[zero_norm_mask] = 0.0
        
        # Create results
        reranked_results = [
            {"score": float(score), "context": ctx}
            for score, ctx in zip(similarities, contexts)
        ]
        
        # Sort by score descending
        reranked_results.sort(key=lambda x: x['score'], reverse=True)
        
        return reranked_results
    
    def compress_context(self, query: str, context: str, threshold: float = 0.5) -> str:
        """
        Extract relevant sentences from context based on similarity to query.
        
        Args:
            query: Search query
            context: Text to compress
            threshold: Minimum similarity score to keep sentence
        
        Returns:
            Compressed context with only relevant sentences
        """
        # Split into sentences
        sentences = context.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return context
        
        # Get embeddings
        query_emb = self.embedder.embed_query(query)
        sent_embs = self.embedder.embed_documents(sentences, task_type="RETRIEVAL_DOCUMENT")
        
        # Calculate similarities
        query_norm = query_emb / np.linalg.norm(query_emb)
        sent_norms = sent_embs / np.linalg.norm(sent_embs, axis=1, keepdims=True)
        similarities = np.dot(sent_norms, query_norm)
        
        # Keep sentences above threshold
        relevant_sentences = [
            sent for sent, score in zip(sentences, similarities)
            if score > threshold
        ]
        
        return '. '.join(relevant_sentences) + '.' if relevant_sentences else context
