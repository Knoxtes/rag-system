#!/usr/bin/env python3

"""
Cleanup script to remove unwanted collections and update file counts
"""

import chromadb
from chromadb.config import Settings
import json
from datetime import datetime

def main():
    print("🧹 Cleaning up collections...")
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path='./chroma_db',
        settings=Settings(allow_reset=True)
    )
    
    # Load current indexed_folders.json
    with open('indexed_folders.json', 'r', encoding='utf-8') as f:
        indexed_folders = json.load(f)
    
    print(f"Found {len(indexed_folders)} indexed folders")
    
    # Collections to remove
    to_remove = []
    
    # Clean up indexed_folders.json
    cleaned_folders = {}
    
    for folder_id, folder_info in indexed_folders.items():
        folder_name = folder_info['name']
        collection_name = folder_info['collection_name']
        files_processed = folder_info['files_processed']
        
        # Check if it's an unknown folder
        if folder_name.startswith("Unknown Folder"):
            print(f"❌ Removing unknown folder: {folder_name} ({files_processed} files)")
            to_remove.append(collection_name)
            continue
        
        # Check if it has 0 files
        if files_processed == 0:
            print(f"❌ Removing empty collection: {folder_name} (0 files)")
            to_remove.append(collection_name)
            continue
        
        # Get actual file count from ChromaDB
        try:
            collection = client.get_collection(collection_name)
            actual_count = collection.count()
            
            # Update file count if different
            if actual_count != files_processed:
                print(f"📊 Updating {folder_name}: {files_processed} → {actual_count} files")
                folder_info['files_processed'] = actual_count
                folder_info['indexed_at'] = datetime.now().isoformat()
            
            # Only keep if it has files
            if actual_count > 0:
                cleaned_folders[folder_id] = folder_info
                print(f"✅ Keeping: {folder_name} ({actual_count} files)")
            else:
                print(f"❌ Removing: {folder_name} (ChromaDB shows 0 files)")
                to_remove.append(collection_name)
                
        except Exception as e:
            print(f"⚠️  Collection {collection_name} not found in ChromaDB, removing from index")
            to_remove.append(collection_name)
    
    # Remove collections from ChromaDB
    print(f"\n🗑️  Removing {len(to_remove)} collections from ChromaDB...")
    for collection_name in to_remove:
        try:
            client.delete_collection(collection_name)
            print(f"  ✓ Deleted {collection_name}")
        except Exception as e:
            print(f"  ⚠️  Could not delete {collection_name}: {e}")
    
    # Save cleaned indexed_folders.json
    with open('indexed_folders.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_folders, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Cleanup complete!")
    print(f"   • Started with: {len(indexed_folders)} collections")
    print(f"   • Removed: {len(to_remove)} collections")
    print(f"   • Remaining: {len(cleaned_folders)} collections")
    
    print("\nRemaining collections:")
    for folder_id, info in cleaned_folders.items():
        print(f"   • {info['name']}: {info['files_processed']} files")

if __name__ == "__main__":
    main()