#!/usr/bin/env python3
"""
Check all ChromaDB collections and show which ones are populated
"""

import chromadb
import json
import os
from pathlib import Path

def check_collections():
    """Check all collections and their stats"""
    
    # Initialize ChromaDB client
    chroma_path = "./chroma_db"
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Get all collections
    collections = client.list_collections()
    
    print("\n" + "=" * 80)
    print("CHROMADB COLLECTION STATUS")
    print("=" * 80)
    print(f"Database location: {os.path.abspath(chroma_path)}")
    print(f"Total collections: {len(collections)}\n")
    
    # Load indexed folders for name mapping
    indexed_folders = {}
    if os.path.exists('indexed_folders.json'):
        with open('indexed_folders.json', 'r') as f:
            indexed_folders = json.load(f)
    
    # Create reverse mapping: collection_name -> folder_info
    collection_to_folder = {}
    for folder_id, folder_info in indexed_folders.items():
        collection_name = folder_info.get('collection_name')
        if collection_name:
            collection_to_folder[collection_name] = folder_info
    
    # Sort collections by document count (descending)
    collection_stats = []
    
    for collection in collections:
        count = collection.count()
        collection_stats.append({
            'name': collection.name,
            'count': count
        })
    
    # Sort by count descending
    collection_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # Display results
    populated = []
    empty = []
    
    for stat in collection_stats:
        collection_name = stat['name']
        count = stat['count']
        
        # Get folder info if available
        folder_info = collection_to_folder.get(collection_name, {})
        folder_name = folder_info.get('name', 'Unknown')
        location = folder_info.get('location', 'Unknown')
        indexed_at = folder_info.get('indexed_at', 'Unknown')
        
        if count > 0:
            populated.append(stat)
            status = "✅ POPULATED"
        else:
            empty.append(stat)
            status = "❌ EMPTY"
        
        print(f"{status}")
        print(f"  Collection: {collection_name}")
        print(f"  Folder: [{location}] {folder_name}")
        print(f"  Documents: {count:,}")
        print(f"  Last Indexed: {indexed_at}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Populated collections: {len(populated)}")
    print(f"❌ Empty collections: {len(empty)}")
    print(f"📊 Total documents across all collections: {sum(s['count'] for s in collection_stats):,}")
    print("=" * 80)
    
    if empty:
        print("\n⚠️  Empty collections detected!")
        print("These collections were likely interrupted during indexing:")
        for stat in empty:
            collection_name = stat['name']
            folder_info = collection_to_folder.get(collection_name, {})
            folder_name = folder_info.get('name', 'Unknown')
            print(f"  - {folder_name} ({collection_name})")
        print("\nYou may want to re-run the indexer for these folders.")
    
    return {
        'populated': populated,
        'empty': empty,
        'total': len(collections)
    }

if __name__ == "__main__":
    try:
        check_collections()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the ChromaDB database exists at ./chroma_db")
