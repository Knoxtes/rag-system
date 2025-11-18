# embeddings.py - Text embedding generation with hybrid search support

from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
from config import (
    EMBEDDING_MODEL, RERANKER_MODEL, USE_HYBRID_SEARCH,
    ENABLE_EMBEDDING_CACHE, EMBEDDING_CACHE_DIR, EMBEDDING_CACHE_TTL_DAYS,
    EMBEDDING_BATCH_SIZE, RERANKING_BATCH_SIZE
)
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple


class LocalEmbedder:
    """Generate embeddings using local models - completely free"""
    
    def __init__(self, model_name=EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"  Model loaded! Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
        # Initialize embedding cache if enabled
        self.cache = None
        if ENABLE_EMBEDDING_CACHE:
            try:
                from embedding_cache import EmbeddingCache
                self.cache = EmbeddingCache(
                    cache_dir=EMBEDDING_CACHE_DIR,
                    ttl_days=EMBEDDING_CACHE_TTL_DAYS
                )
                print(f"  ✓ Embedding cache enabled: {self.cache}")
            except ImportError:
                print("  ⚠️  embedding_cache module not found, caching disabled")
                print("     Install with: pip install diskcache")
    
    def embed_documents(self, texts):
        """Generate embeddings for multiple documents with caching and batching"""
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
        
        # Generate embeddings for uncached texts in batches
        new_embeddings = []
        if uncached_texts:
            print(f"  Generating embeddings for {len(uncached_texts)} chunks (batch_size={EMBEDDING_BATCH_SIZE})...")
            
            for i in range(0, len(uncached_texts), EMBEDDING_BATCH_SIZE):
                batch = uncached_texts[i:i + EMBEDDING_BATCH_SIZE]
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    batch_size=EMBEDDING_BATCH_SIZE
                )
                new_embeddings.extend(batch_embeddings)
            
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
    
    def embed_query(self, query):
        """Generate embedding for a single query"""
        return self.model.encode(
            query, 
            convert_to_numpy=True,
            normalize_embeddings=True  # ADDED: Normalize for consistency
        )

# --- ENHANCED: Re-ranker class with contextual compression ---
class LocalReranker:
    """
    Reranks documents based on relevance using a local CrossEncoder model.
    Also supports contextual compression to extract only relevant sentences.
    """
    def __init__(self, model_name=RERANKER_MODEL):
        print(f"Loading re-ranking model: {model_name}")
        self.model = CrossEncoder(model_name)
        print("  Re-ranker loaded!")

    def rerank(self, query: str, contexts: List[str], return_scores: bool = True) -> List[Dict]:
        """
        Reranks a list of context strings based on a query with batch processing.
        
        Args:
            query: Search query
            contexts: List of text chunks to rerank
            return_scores: If True, include scores in results
        
        Returns:
            List of dictionaries with score and context, sorted by relevance
        """
        if not contexts:
            return []
            
        # Create pairs of [query, context]
        query_chunk_pairs = [[query, ctx] for ctx in contexts]
        
        # Predict relevance scores in batches for better performance
        all_scores = []
        for i in range(0, len(query_chunk_pairs), RERANKING_BATCH_SIZE):
            batch = query_chunk_pairs[i:i + RERANKING_BATCH_SIZE]
            scores = self.model.predict(batch, show_progress_bar=False)
            all_scores.extend(scores)
        
        # Combine scores with original contexts
        reranked_results = [
            {"score": float(score), "context": ctx}
            for score, ctx in zip(all_scores, contexts)
        ]
        
        # Sort by score in descending order
        reranked_results.sort(key=lambda x: x['score'], reverse=True)
        
        return reranked_results
    
    def compress_context(self, query: str, context: str, threshold: float = 0.3) -> str:
        """
        Extract only sentences from context that are relevant to the query.
        Useful for reducing noise in long chunks.
        
        Args:
            query: Search query
            context: Text chunk to compress
            threshold: Minimum relevance score (0-1) to keep a sentence
        
        Returns:
            Compressed context with only relevant sentences
        """
        # Split into sentences
        sentences = context.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return context
        
        # Score each sentence
        pairs = [[query, sent] for sent in sentences]
        scores = self.model.predict(pairs)
        
        # Keep sentences above threshold
        relevant_sentences = [
            sent for sent, score in zip(sentences, scores) 
            if score > threshold
        ]
        
        # Return compressed context, or full context if nothing passed
        return '. '.join(relevant_sentences) + '.' if relevant_sentences else context


# --- NEW: Hybrid search combining BM25 and dense embeddings ---
class HybridSearcher:
    """
    Combines BM25 (keyword-based) and dense embeddings (semantic) for better retrieval.
    Particularly useful for:
    - Acronyms and exact matches (BM25)
    - Semantic similarity (dense embeddings)
    - Domain-specific terminology
    """
    
    def __init__(self, corpus: List[str] = None):
        """
        Initialize BM25 index with a corpus.
        
        Args:
            corpus: List of text chunks to index
        """
        self.corpus = corpus or []
        self.bm25 = None
        self.tokenized_corpus = []
        
        if corpus:
            self._build_index(corpus)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - split on whitespace and lowercase"""
        return text.lower().split()
    
    def _build_index(self, corpus: List[str]):
        """Build BM25 index from corpus"""
        self.corpus = corpus
        self.tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def search(self, query: str, top_k: int = 100) -> List[Tuple[int, float]]:
        """
        Search using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (index, score) tuples sorted by relevance
        """
        if not self.bm25:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top K indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [(int(idx), float(scores[idx])) for idx in top_indices]
    
    def update_corpus(self, corpus: List[str]):
        """Update the BM25 index with new corpus"""
        self._build_index(corpus)

