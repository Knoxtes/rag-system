# advanced_caching.py - Semantic similarity-based intelligent caching system

import numpy as np
import json
import time
import hashlib
import pickle
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Enhanced cache entry with semantic metadata"""
    query: str
    query_embedding: np.ndarray
    response: Dict[str, Any]
    timestamp: float
    access_count: int
    confidence_score: float
    source_files: List[str]
    query_type: str
    cost_saved: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization (excluding embedding)"""
        data = asdict(self)
        data.pop('query_embedding')  # Can't serialize numpy array to JSON
        return data

@dataclass
class QueryAnalysis:
    """Query analysis for intelligent caching decisions"""
    query_type: str  # 'search', 'synthesis', 'summary', 'comparison'
    complexity_score: float  # 0-1, higher = more complex
    expected_cost: float  # Estimated API cost
    cache_priority: float  # 0-1, higher = more likely to cache
    similar_patterns: List[str]  # Similar query patterns


class SemanticQueryCache:
    """
    Advanced caching system using semantic similarity.
    Caches by meaning rather than exact text matching.
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,
                 max_cache_size: int = 2000,
                 ttl_seconds: int = 3600,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
            max_cache_size: Maximum number of cached entries
            ttl_seconds: Time to live for cache entries
            embedding_model: SentenceTransformer model for query embeddings
        """
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        
        # Load embedding model (lightweight for query analysis)
        logger.info(f"Loading cache embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.query_embeddings = np.array([])  # For batch similarity search
        self.cache_keys = []  # Corresponding keys for embeddings
        
        # Performance metrics
        self.stats = {
            'hits': 0,
            'misses': 0, 
            'total_queries': 0,
            'cost_saved': 0.0,
            'time_saved': 0.0
        }
        
        logger.info("Semantic cache initialized")
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate unique key for cache entry"""
        normalized_query = query.lower().strip()
        return hashlib.sha256(normalized_query.encode()).hexdigest()[:16]
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query to determine caching priority and expected cost.
        """
        query_lower = query.lower()
        
        # Detect query type
        query_type = "search"  # default
        if any(word in query_lower for word in ['summarize', 'summary', 'overview']):
            query_type = "synthesis"
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            query_type = "comparison"
        elif any(word in query_lower for word in ['list', 'show all', 'what are']):
            query_type = "listing"
        
        # Calculate complexity score (affects API cost)
        complexity_factors = [
            len(query.split()) / 20.0,  # Length factor
            1.0 if 'all' in query_lower else 0.0,  # Scope factor
            1.0 if any(word in query_lower for word in ['summarize', 'compare']) else 0.0,  # Synthesis factor
            0.5 if '?' in query else 0.0,  # Question factor
        ]
        complexity_score = min(sum(complexity_factors), 1.0)
        
        # Estimate API cost (based on complexity and expected context size)
        base_cost = 0.001  # Base API call cost
        complexity_multiplier = 1 + (complexity_score * 3)  # 1x to 4x
        expected_cost = base_cost * complexity_multiplier
        
        # Cache priority (higher complexity = higher priority)
        cache_priority = complexity_score * 0.7 + (0.3 if query_type in ['synthesis', 'comparison'] else 0.0)
        
        # Find similar patterns
        similar_patterns = []
        for cached_key in self.cache_keys[-50:]:  # Check recent queries only
            cached_entry = self.cache.get(cached_key)
            if cached_entry and cached_entry.query_type == query_type:
                similar_patterns.append(cached_entry.query)
        
        return QueryAnalysis(
            query_type=query_type,
            complexity_score=complexity_score,
            expected_cost=expected_cost,
            cache_priority=cache_priority,
            similar_patterns=similar_patterns[:5]  # Top 5 similar
        )
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
            # Remove from embeddings array (rebuild if many deletions)
            if key in self.cache_keys:
                idx = self.cache_keys.index(key)
                self.cache_keys.pop(idx)
                self.query_embeddings = np.delete(self.query_embeddings, idx, axis=0)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_least_valuable(self):
        """Evict least valuable entries when cache is full"""
        if len(self.cache) <= self.max_cache_size:
            return
        
        # Calculate value score for each entry
        current_time = time.time()
        entry_scores = []
        
        for key, entry in self.cache.items():
            # Value factors: access frequency, recency, query complexity, cost saved
            age_factor = max(0, 1 - ((current_time - entry.timestamp) / self.ttl_seconds))
            access_factor = min(entry.access_count / 10.0, 1.0)
            cost_factor = min(entry.cost_saved / 0.01, 1.0)  # Up to $0.01 saved
            confidence_factor = entry.confidence_score
            
            value_score = (age_factor * 0.3 + access_factor * 0.3 + 
                          cost_factor * 0.2 + confidence_factor * 0.2)
            entry_scores.append((key, value_score))
        
        # Sort by value and remove lowest 20%
        entry_scores.sort(key=lambda x: x[1])
        remove_count = len(self.cache) - self.max_cache_size + 100  # Remove extra for buffer
        
        for key, _ in entry_scores[:remove_count]:
            if key in self.cache:
                del self.cache[key]
                if key in self.cache_keys:
                    idx = self.cache_keys.index(key)
                    self.cache_keys.pop(idx)
                    self.query_embeddings = np.delete(self.query_embeddings, idx, axis=0)
        
        logger.info(f"Evicted {remove_count} low-value cache entries")
    
    def _find_similar_query(self, query_embedding: np.ndarray, threshold: float = None) -> Optional[Tuple[str, float]]:
        """
        Find cached query with highest similarity above threshold.
        
        Returns:
            (cache_key, similarity_score) or None
        """
        if len(self.cache_keys) == 0 or self.query_embeddings.size == 0:
            return None
        
        threshold = threshold or self.similarity_threshold
        
        # Calculate cosine similarities
        similarities = cosine_similarity([query_embedding], self.query_embeddings)[0]
        
        # Find best match above threshold
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]
        
        if best_similarity >= threshold:
            best_key = self.cache_keys[best_idx]
            return (best_key, best_similarity)
        
        return None
    
    def get(self, query: str, analysis: QueryAnalysis = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response for semantically similar query.
        
        Args:
            query: User query
            analysis: Optional pre-computed query analysis
            
        Returns:
            Cached response or None
        """
        self.stats['total_queries'] += 1
        
        # Clean up expired entries periodically
        if self.stats['total_queries'] % 100 == 0:
            self._cleanup_expired()
        
        # Analyze query if not provided
        if analysis is None:
            analysis = self._analyze_query(query)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query, normalize_embeddings=True)
        
        # Find similar cached query
        similar_result = self._find_similar_query(query_embedding)
        
        if similar_result:
            cache_key, similarity = similar_result
            cached_entry = self.cache.get(cache_key)
            
            if cached_entry:
                # Update access stats
                cached_entry.access_count += 1
                cached_entry.cost_saved += analysis.expected_cost
                
                # Update global stats
                self.stats['hits'] += 1
                self.stats['cost_saved'] += analysis.expected_cost
                self.stats['time_saved'] += 2.0  # Assume 2s saved per cache hit
                
                logger.info(f"Cache HIT: {similarity:.3f} similarity for '{query[:50]}...'")
                logger.info(f"  → Using cached result from: '{cached_entry.query[:50]}...'")
                logger.info(f"  → Cost saved: ${analysis.expected_cost:.4f}")
                
                return cached_entry.response
        
        self.stats['misses'] += 1
        logger.info(f"Cache MISS for '{query[:50]}...'")
        return None
    
    def set(self, 
            query: str, 
            response: Dict[str, Any], 
            confidence_score: float = 1.0,
            analysis: QueryAnalysis = None) -> bool:
        """
        Cache a query response with semantic indexing.
        
        Args:
            query: Original user query
            response: LLM response to cache
            confidence_score: Quality score 0-1 (affects caching priority)
            analysis: Optional pre-computed query analysis
            
        Returns:
            True if cached successfully
        """
        # Don't cache low-confidence or error responses
        if confidence_score < 0.7 or not response or 'error' in response:
            logger.info(f"Skipping cache for low-confidence response: {confidence_score:.2f}")
            return False
        
        # Analyze query if not provided
        if analysis is None:
            analysis = self._analyze_query(query)
        
        # Skip caching for low-priority queries
        if analysis.cache_priority < 0.3:
            logger.info(f"Skipping cache for low-priority query: {analysis.cache_priority:.2f}")
            return False
        
        # Generate embeddings
        query_embedding = self.embedding_model.encode(query, normalize_embeddings=True)
        cache_key = self._generate_cache_key(query)
        
        # Extract source files from response
        source_files = []
        if 'answer' in response and isinstance(response['answer'], str):
            # Simple extraction - could be enhanced
            answer_text = response['answer']
            if 'source_path' in str(response):
                # Extract from structured response
                pass  # Could parse structured source info
        
        # Create cache entry
        cache_entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            response=response,
            timestamp=time.time(),
            access_count=1,
            confidence_score=confidence_score,
            source_files=source_files,
            query_type=analysis.query_type,
            cost_saved=analysis.expected_cost
        )
        
        # Evict if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._evict_least_valuable()
        
        # Store in cache
        self.cache[cache_key] = cache_entry
        self.cache_keys.append(cache_key)
        
        # Update embeddings array
        if self.query_embeddings.size == 0:
            self.query_embeddings = np.array([query_embedding])
        else:
            self.query_embeddings = np.vstack([self.query_embeddings, query_embedding])
        
        logger.info(f"Cached response for '{query[:50]}...' (priority: {analysis.cache_priority:.2f})")
        return True
    
    def invalidate_by_source(self, source_patterns: List[str]):
        """
        Invalidate cache entries that reference specific sources.
        Useful when documents are updated.
        
        Args:
            source_patterns: List of file patterns to invalidate
        """
        invalidated_keys = []
        
        for key, entry in list(self.cache.items()):
            # Check if any source file matches patterns
            should_invalidate = False
            for pattern in source_patterns:
                for source_file in entry.source_files:
                    if pattern.lower() in source_file.lower():
                        should_invalidate = True
                        break
                if should_invalidate:
                    break
            
            if should_invalidate:
                invalidated_keys.append(key)
                del self.cache[key]
                if key in self.cache_keys:
                    idx = self.cache_keys.index(key)
                    self.cache_keys.pop(idx)
                    self.query_embeddings = np.delete(self.query_embeddings, idx, axis=0)
        
        if invalidated_keys:
            logger.info(f"Invalidated {len(invalidated_keys)} cache entries for sources: {source_patterns}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        total_queries = self.stats['total_queries']
        hit_rate = (self.stats['hits'] / total_queries) if total_queries > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_cache_size,
            'total_queries': total_queries,
            'cache_hits': self.stats['hits'],
            'cache_misses': self.stats['misses'],
            'hit_rate_percent': hit_rate * 100,
            'total_cost_saved': self.stats['cost_saved'],
            'total_time_saved': self.stats['time_saved'],
            'average_cost_per_query': self.stats['cost_saved'] / max(self.stats['hits'], 1),
            'similarity_threshold': self.similarity_threshold,
            'ttl_hours': self.ttl_seconds / 3600,
        }
    
    def warm_cache(self, common_queries: List[str]):
        """
        Pre-warm cache with common queries.
        Useful for anticipating frequent user queries.
        """
        logger.info(f"Warming cache with {len(common_queries)} common queries")
        # This would need integration with the main RAG system
        # to actually execute queries and cache responses
        pass
    
    def export_cache(self, filepath: str):
        """Export cache to file for persistence"""
        cache_data = {
            'entries': {key: entry.to_dict() for key, entry in self.cache.items()},
            'stats': self.stats,
            'config': {
                'similarity_threshold': self.similarity_threshold,
                'max_cache_size': self.max_cache_size,
                'ttl_seconds': self.ttl_seconds
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Cache exported to {filepath}")
    
    def import_cache(self, filepath: str):
        """Import cache from file"""
        try:
            with open(filepath, 'r') as f:
                cache_data = json.load(f)
            
            # Rebuild cache (without embeddings - they'll be regenerated)
            for key, entry_data in cache_data.get('entries', {}).items():
                # Regenerate embeddings
                query_embedding = self.embedding_model.encode(
                    entry_data['query'], 
                    normalize_embeddings=True
                )
                
                # Reconstruct entry
                entry = CacheEntry(
                    query=entry_data['query'],
                    query_embedding=query_embedding,
                    response=entry_data['response'],
                    timestamp=entry_data['timestamp'],
                    access_count=entry_data['access_count'],
                    confidence_score=entry_data['confidence_score'],
                    source_files=entry_data['source_files'],
                    query_type=entry_data['query_type'],
                    cost_saved=entry_data.get('cost_saved', 0.0)
                )
                
                self.cache[key] = entry
                self.cache_keys.append(key)
                
                if self.query_embeddings.size == 0:
                    self.query_embeddings = np.array([query_embedding])
                else:
                    self.query_embeddings = np.vstack([self.query_embeddings, query_embedding])
            
            # Import stats
            self.stats.update(cache_data.get('stats', {}))
            
            logger.info(f"Cache imported from {filepath}: {len(self.cache)} entries")
            
        except Exception as e:
            logger.error(f"Failed to import cache: {e}")


class ProactiveCacheWarmer:
    """
    Analyzes query patterns to predict and pre-cache likely queries.
    Reduces latency for anticipated requests.
    """
    
    def __init__(self, cache: SemanticQueryCache):
        self.cache = cache
        self.query_patterns = {}
        self.seasonal_patterns = {}
    
    def analyze_query_patterns(self, recent_queries: List[str]):
        """Analyze recent queries to identify patterns"""
        # Implementation for pattern detection
        # Could use clustering or frequency analysis
        pass
    
    def predict_next_queries(self) -> List[str]:
        """Predict likely next queries based on patterns"""
        # Implementation for query prediction
        # Could use time-series analysis or collaborative filtering
        return []
    
    def warm_predicted_queries(self):
        """Pre-execute predicted queries to warm cache"""
        predicted = self.predict_next_queries()
        # Would execute these queries in background
        pass


# Example usage and testing
if __name__ == "__main__":
    # Initialize semantic cache
    cache = SemanticQueryCache(
        similarity_threshold=0.85,
        max_cache_size=1000,
        ttl_seconds=3600
    )
    
    # Test queries with semantic similarity
    test_queries = [
        "What are the Q1 sales figures for Elmira?",
        "Show me Q1 sales data for Elmira market",  # Similar to above
        "List all projects in 2025 January folder",
        "What projects are in the January 2025 directory?",  # Similar to above
        "Compare Mansfield and Elmira markets",
        "How do Mansfield and Elmira markets differ?",  # Similar to above
    ]
    
    # Simulate cache usage
    for i, query in enumerate(test_queries):
        print(f"\nQuery {i+1}: {query}")
        
        analysis = cache._analyze_query(query)
        print(f"  Type: {analysis.query_type}, Priority: {analysis.cache_priority:.2f}")
        
        # Check cache
        result = cache.get(query, analysis)
        if result:
            print("  → Cache HIT!")
        else:
            print("  → Cache MISS")
            
            # Simulate response and cache it
            fake_response = {
                'answer': f"Response for: {query}",
                'query_type': analysis.query_type
            }
            cache.set(query, fake_response, confidence_score=0.9, analysis=analysis)
            print("  → Response cached")
    
    # Print cache statistics
    stats = cache.get_cache_stats()
    print(f"\n=== Cache Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")