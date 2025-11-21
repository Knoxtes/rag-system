#!/usr/bin/env python3

"""
Complete database cleanup and fresh re-indexing
"""

import chromadb
from chromadb.config import Settings
import os
import shutil
import json

def main():
    print("🧹 Complete database cleanup and re-indexing...")
    
    # 1. Stop any running processes first
    print("\n1. Cleaning up ChromaDB...")
    
    # Clear ChromaDB completely
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
            print("   ✓ ChromaDB reset complete")
            
        except Exception as e:
            print(f"   ⚠️  Error during ChromaDB cleanup: {e}")
            print("   Trying to delete ChromaDB directory...")
            
            # If that fails, delete the entire directory
            try:
                shutil.rmtree(chroma_dir)
                print("   ✓ ChromaDB directory deleted")
            except Exception as e2:
                print(f"   ❌ Could not delete ChromaDB directory: {e2}")
    
    # 2. Clear indexed_folders.json
    print("\n2. Clearing indexed_folders.json...")
    indexed_file = 'indexed_folders.json'
    if os.path.exists(indexed_file):
        os.remove(indexed_file)
        print("   ✓ indexed_folders.json deleted")
    else:
        print("   ✓ indexed_folders.json not found (already clean)")
    
    # 3. Clear embedding cache if exists
    print("\n3. Clearing embedding cache...")
    cache_dirs = ['./embedding_cache', './csv_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✓ Deleted {cache_dir}")
            except Exception as e:
                print(f"   ⚠️  Could not delete {cache_dir}: {e}")
        else:
            print(f"   ✓ {cache_dir} not found")
    
    # 4. Clear any backup directories that might interfere
    print("\n4. Checking for backup directories...")
    backup_dirs = ['./chroma_db_backups']
    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            print(f"   📁 Found backup directory: {backup_dir} (keeping for safety)")
        else:
            print(f"   ✓ No backup directory found")
    
    print("\n✅ Database cleanup complete!")
    print("\nNow running fresh indexing...")
    print("=" * 50)
    
    # 5. Run the batch indexer for a fresh start
    import subprocess
    try:
        result = subprocess.run(['python', 'batch_index_all.py'], 
                              capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ Fresh indexing completed successfully!")
            print(result.stdout)
        else:
            print("❌ Indexing failed:")
            print(result.stderr)
            print(result.stdout)
    
    except subprocess.TimeoutExpired:
        print("⏰ Indexing timed out (30 minutes) - this might be normal for large datasets")
    except Exception as e:
        print(f"❌ Error running indexer: {e}")
        print("\nYou can manually run the indexer with:")
        print("   python batch_index_all.py")
    
    print("\n🎉 Complete cleanup and re-indexing finished!")

if __name__ == "__main__":
    main()