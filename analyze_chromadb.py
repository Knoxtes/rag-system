#!/usr/bin/env python3
"""
Analyze ChromaDB collections - find empty/redundant collections
"""

import chromadb
from pathlib import Path

def analyze_chromadb():
    """Check all ChromaDB collections for size and content"""
    
    print("🔍 Analyzing ChromaDB Collections...")
    print("=" * 70)
    
    chroma_path = "./chroma_db"
    
    if not Path(chroma_path).exists():
        print("❌ ChromaDB directory not found!")
        return
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Get all collections
    collections = client.list_collections()
    
    if not collections:
        print("No collections found!")
        return
    
    print(f"Found {len(collections)} collections\n")
    
    empty_collections = []
    small_collections = []
    total_documents = 0
    
    for collection in collections:
        name = collection.name
        count = collection.count()
        total_documents += count
        
        # Get size estimate (approximate)
        collection_path = Path(chroma_path) / name
        if collection_path.exists():
            size_mb = sum(f.stat().st_size for f in collection_path.rglob('*') if f.is_file()) / (1024 * 1024)
        else:
            size_mb = 0
        
        status = "✅"
        notes = ""
        
        if count == 0:
            status = "❌ EMPTY"
            empty_collections.append(name)
            notes = " - Can be deleted"
        elif count < 5:
            status = "⚠️  SMALL"
            small_collections.append((name, count))
            notes = f" - Only {count} documents"
        
        print(f"{status} {name}")
        print(f"   Documents: {count:,}")
        print(f"   Size: {size_mb:.2f} MB{notes}")
        print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Collections: {len(collections)}")
    print(f"Total Documents: {total_documents:,}")
    print(f"Empty Collections: {len(empty_collections)}")
    print(f"Small Collections: {len(small_collections)}")
    
    if empty_collections:
        print("\n🗑️  EMPTY COLLECTIONS (can be deleted):")
        for name in empty_collections:
            print(f"   - {name}")
    
    if small_collections:
        print("\n⚠️  SMALL COLLECTIONS (consider if needed):")
        for name, count in small_collections:
            print(f"   - {name}: {count} documents")
    
    # Calculate potential space savings
    if empty_collections or small_collections:
        print("\n💡 RECOMMENDATIONS:")
        if empty_collections:
            print(f"   • Delete {len(empty_collections)} empty collection(s) to save space")
        if small_collections:
            print(f"   • Review {len(small_collections)} small collection(s) - may be incomplete")
    else:
        print("\n✅ All collections are healthy and populated!")
    
    print("=" * 70)

if __name__ == '__main__':
    analyze_chromadb()
