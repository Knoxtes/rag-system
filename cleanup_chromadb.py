#!/usr/bin/env python3
"""
Clean up empty ChromaDB collections
"""

import chromadb
from pathlib import Path
import shutil

def cleanup_chromadb():
    """Delete empty collections from ChromaDB"""
    
    print("🧹 Cleaning up ChromaDB...")
    print("=" * 70)
    
    chroma_path = "./chroma_db"
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Collections to delete (from analysis)
    empty_collections = [
        'test_optimization',
        'folder_1XV-uj4yti8Cw-EN_t8Kpma9NaJPGQJZ2',
        'test_pool_1',
        'folder_1ST8F13mAslBww8Gc3xatK2jr8Y3E5fOa'
    ]
    
    total_deleted = 0
    space_saved = 0
    
    for collection_name in empty_collections:
        try:
            # Get collection
            collection = client.get_collection(collection_name)
            count = collection.count()
            
            # Double-check it's empty
            if count == 0:
                # Calculate size before deletion
                collection_path = Path(chroma_path) / collection_name
                if collection_path.exists():
                    size_mb = sum(f.stat().st_size for f in collection_path.rglob('*') if f.is_file()) / (1024 * 1024)
                    space_saved += size_mb
                
                # Delete collection
                client.delete_collection(collection_name)
                print(f"✅ Deleted: {collection_name} (was empty)")
                total_deleted += 1
            else:
                print(f"⚠️  Skipped: {collection_name} (not empty: {count} docs)")
                
        except Exception as e:
            print(f"❌ Error deleting {collection_name}: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ Cleanup complete!")
    print(f"   Deleted: {total_deleted} empty collections")
    print(f"   Space saved: ~{space_saved:.2f} MB")
    print("=" * 70)

if __name__ == '__main__':
    response = input("Delete 4 empty collections? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup_chromadb()
    else:
        print("❌ Cleanup cancelled")
