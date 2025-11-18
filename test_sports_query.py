#!/usr/bin/env python3
"""
Test querying the Sports collection to diagnose issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system import EnhancedRAGSystem

def test_sports_collection():
    print("Testing Sports Collection Query")
    print("=" * 80)
    
    # Initialize RAG for Sports collection
    collection_name = "folder_17tKM1qfm2xL3AX-DZStoR6aKZI62mUbb"
    
    try:
        print(f"\n1. Initializing RAG system for: {collection_name}")
        rag = EnhancedRAGSystem(drive_service=None, collection_name=collection_name)
        print(f"   ✓ Initialized successfully")
        print(f"   Documents in collection: {rag.vector_store.collection.count()}")
        
        # Test query
        query = "Summarize the 7MM Sports Schedule"
        print(f"\n2. Testing query: '{query}'")
        print("-" * 80)
        
        response = rag.query(query)
        
        print(f"\n3. Response:")
        print("-" * 80)
        print(response.get('answer', 'No answer'))
        
        print(f"\n4. Sources used:")
        print("-" * 80)
        for i, source in enumerate(response.get('sources', []), 1):
            print(f"   {i}. {source.get('title', 'Unknown')}")
            print(f"      URL: {source.get('url', 'N/A')}")
            print(f"      Relevance: {source.get('relevance_score', 'N/A')}")
        
        print(f"\n5. Search Results Retrieved:")
        print("-" * 80)
        print(f"   Total results: {len(response.get('sources', []))}")
        
        # Check what's actually in the collection
        print(f"\n6. Collection Contents:")
        print("-" * 80)
        data = rag.vector_store.collection.get(include=['documents', 'metadatas'], limit=5)
        for i, (doc, meta) in enumerate(zip(data['documents'], data['metadatas']), 1):
            print(f"   Chunk {i}:")
            print(f"   File: {meta.get('file_name', 'Unknown')}")
            print(f"   Preview: {doc[:200]}...")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sports_collection()
