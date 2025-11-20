#!/usr/bin/env python3

"""
Simple database cleanup only - no subprocess calls
"""

import chromadb
from chromadb.config import Settings
import os
import shutil
import json

def main():
    print("🧹 Complete database cleanup...")
    
    # 1. Clear ChromaDB completely
    print("\n1. Cleaning up ChromaDB...")
    
    chroma_dir = './chroma_db'
    if os.path.exists(chroma_dir):
        try:
            # Try to delete collections first
            client = chromadb.PersistentClient(
                path=chroma_dir,
                settings=Settings(allow_reset=True)
            )
            
            collections = client.list_collections()
            print(f"   Found {len(collections)} existing collections")
            
            for col in collections:
                try:
                    client.delete_collection(col.name)
                    print(f"   ✓ Deleted collection: {col.name}")
                except:
                    pass
            
            # Reset the entire database
            client.reset()
            print("   ✅ ChromaDB reset complete")
            
        except Exception as e:
            print(f"   ⚠️  Error during ChromaDB cleanup: {e}")
            print("   Trying to delete ChromaDB directory...")
            
            # If that fails, delete the entire directory
            try:
                shutil.rmtree(chroma_dir)
                print("   ✅ ChromaDB directory deleted")
            except Exception as e2:
                print(f"   ❌ Could not delete ChromaDB directory: {e2}")
    else:
        print("   ✅ ChromaDB directory not found (already clean)")
    
    # 2. Clear indexed_folders.json
    print("\n2. Clearing indexed_folders.json...")
    indexed_file = 'indexed_folders.json'
    if os.path.exists(indexed_file):
        os.remove(indexed_file)
        print("   ✅ indexed_folders.json deleted")
    else:
        print("   ✅ indexed_folders.json not found (already clean)")
    
    # 3. Clear embedding cache if exists
    print("\n3. Clearing embedding cache...")
    cache_dirs = ['./embedding_cache', './csv_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Deleted {cache_dir}")
            except Exception as e:
                print(f"   ⚠️  Could not delete {cache_dir}: {e}")
        else:
            print(f"   ✅ {cache_dir} not found")
    
    print("\n✅ Database cleanup complete!")
    print("\n📋 Next steps:")
    print("   1. Run: python console_indexer.py --list-folders")
    print("   2. Run: python batch_index_all.py")
    print("   3. Run: python create_indexed_folders_fixed.py")
    print("   4. Restart your server")

if __name__ == "__main__":
    main()