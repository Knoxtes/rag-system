# embeddings.py - Text embedding generation with hybrid search support

from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
from config import EMBEDDING_MODEL, RERANKER_MODEL, USE_HYBRID_SEARCH
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple


class LocalEmbedder:
    """Generate embeddings using local models - completely free"""
    
    def __init__(self, model_name=EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"  Model loaded! Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed_documents(self, texts):
        """Generate embeddings for multiple documents"""
        if not texts:
            return np.array([])
        
        print(f"  Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # ADDED: Normalize for better cosine similarity
        )
        return embeddings
    
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
        Reranks a list of context strings based on a query.
        
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
        
        # Predict relevance scores
        scores = self.model.predict(query_chunk_pairs)
        
        # Combine scores with original contexts
        reranked_results = [
            {"score": float(score), "context": ctx}
            for score, ctx in zip(scores, contexts)
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

