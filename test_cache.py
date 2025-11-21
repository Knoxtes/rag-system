#!/usr/bin/env python3
"""
Quick test to verify query caching is working
"""

import time
from redis_cache import RedisQueryCache
from semantic_cache import SemanticQueryCache

# Test Redis cache
print("=" * 60)
print("Testing Redis Cache")
print("=" * 60)

cache = RedisQueryCache()

# Test set and get
test_query = "What is our vacation policy?"
test_result = {
    'answer': 'Test answer about vacation policy',
    'sources': [{'title': 'HR Handbook'}],
    'search_time': 5.2
}

print(f"\n1. Storing answer in cache...")
cache.set(test_query, test_result, ttl=900)
print(f"   ✓ Stored")

print(f"\n2. Retrieving from cache (should be instant)...")
start = time.time()
cached = cache.get(test_query)
elapsed = (time.time() - start) * 1000  # milliseconds

if cached:
    print(f"   ✓ Retrieved in {elapsed:.2f}ms")
    print(f"   Answer: {cached['answer'][:50]}...")
    print(f"   Sources: {len(cached['sources'])}")
else:
    print(f"   ✗ Cache miss (unexpected!)")

print(f"\n3. Cache stats:")
print(f"   Hits: {cache.stats['hits']}")
print(f"   Misses: {cache.stats['misses']}")
print(f"   Hit rate: {cache.stats['hits']/(cache.stats['total_requests'] or 1)*100:.1f}%")

# Test semantic cache
print("\n" + "=" * 60)
print("Testing Semantic Cache")
print("=" * 60)

sem_cache = SemanticQueryCache()

print(f"\n1. Storing answer in semantic cache...")
sem_cache.set(test_query, test_result)
print(f"   ✓ Stored")

print(f"\n2. Testing exact match...")
start = time.time()
cached = sem_cache.get(test_query)
elapsed = (time.time() - start) * 1000

if cached:
    print(f"   ✓ Retrieved in {elapsed:.2f}ms")
else:
    print(f"   ✗ Cache miss")

print(f"\n3. Testing similar query (should match with >90% similarity)...")
similar_query = "What is our PTO policy?"
start = time.time()
cached = sem_cache.get(similar_query)
elapsed = (time.time() - start) * 1000

if cached:
    print(f"   ✓ Retrieved in {elapsed:.2f}ms (semantic match)")
else:
    print(f"   ✗ No semantic match found")

print("\n" + "=" * 60)
print("Cache Test Complete!")
print("=" * 60)
