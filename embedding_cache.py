# embedding_cache.py - Disk-based embedding cache for performance

import diskcache as dc
import hashlib
import numpy as np
import os

class EmbeddingCache:
    """
    Disk-based cache for embeddings to avoid recomputing.
    Saves significant CPU time for repeated documents.
    """
    
    def __init__(self, cache_dir="./embedding_cache", ttl_days=7):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time-to-live in days (default 7)
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = dc.Cache(cache_dir)
        self.ttl_seconds = ttl_days * 86400
        self.hits = 0
        self.misses = 0
    
    def _get_key(self, text):
        """Generate cache key from text"""
        return f"emb_{hashlib.md5(text.encode('utf-8')).hexdigest()}"
    
    def get(self, text):
        """
        Get embedding from cache.
        
        Args:
            text: Document text
            
        Returns:
            numpy array of embedding, or None if not cached
        """
        key = self._get_key(text)
        result = self.cache.get(key)
        
        if result is not None:
            self.hits += 1
            return np.array(result)
        else:
            self.misses += 1
            return None
    
    def set(self, text, embedding):
        """
        Store embedding in cache.
        
        Args:
            text: Document text
            embedding: Embedding vector (numpy array or list)
        """
        key = self._get_key(text)
        # Handle both numpy arrays and lists
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
        self.cache.set(key, embedding, expire=self.ttl_seconds)
    
    def get_batch(self, texts):
        """
        Get multiple embeddings from cache.
        
        Args:
            texts: List of document texts
            
        Returns:
            List of embeddings (None for cache misses)
        """
        return [self.get(text) for text in texts]
    
    def set_batch(self, texts, embeddings):
        """
        Store multiple embeddings in cache.
        
        Args:
            texts: List of document texts
            embeddings: List of embedding vectors
        """
        for text, emb in zip(texts, embeddings):
            self.set(text, emb)
    
    def clear(self):
        """Clear all cached embeddings"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_entries': len(self.cache)
        }
    
    def __repr__(self):
        stats = self.get_stats()
        return f"EmbeddingCache(entries={stats['total_entries']}, hit_rate={stats['hit_rate']})"


if __name__ == "__main__":
    # Test the cache
    cache = EmbeddingCache()
    
    # Test single embedding
    test_text = "This is a test document"
    test_embedding = np.random.rand(384)
    
    print("Testing embedding cache...")
    print(f"Initial stats: {cache.get_stats()}")
    
    # Set and get
    cache.set(test_text, test_embedding)
    retrieved = cache.get(test_text)
    
    print(f"Embedding stored: {test_embedding[:5]}")
    print(f"Embedding retrieved: {retrieved[:5]}")
    print(f"Match: {np.allclose(test_embedding, retrieved)}")
    
    # Test batch operations
    texts = [f"Document {i}" for i in range(10)]
    embeddings = [np.random.rand(384) for _ in range(10)]
    
    cache.set_batch(texts, embeddings)
    retrieved_batch = cache.get_batch(texts)
    
    print(f"\nBatch test: {len([x for x in retrieved_batch if x is not None])}/10 retrieved")
    print(f"Final stats: {cache.get_stats()}")
