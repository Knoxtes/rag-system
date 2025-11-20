#!/usr/bin/env python3

"""
Create indexed_folders.json with the correct folder mapping
"""

import chromadb
from chromadb.config import Settings
import json
from datetime import datetime

# Known folder mapping from console_indexer.py --list-folders
FOLDER_MAPPING = {
    "1tiS_9s-BB--qX_w1jbT2eg2lHaikFaMo": "Market Resources",
    "1uEfnwP1zKT2D-E5F854qU38pt35vGysR": "Admin/Traffic", 
    "17tKM1qfm2xL3AX-DZStoR6aKZI62mUbb": "Sports",
    "1pavO4fb0UC3M9wvTmO_Ha4XEpc41JBCG": "Sales",
    "1I60lMExM4aWG9GeLwqlj0KbZp8B-lCIl": "Human Resources",
    "1xMZjA6iuAy3sScRpkrh2Q4Ss4MEt3x3P": "Digital",
    "1T2UYUSHd4aX_F-_fBkTN0IyoXwYze_rw": "Programming",
    "1ST8F13mAslBww8Gc3xatK2jr8Y3E5fOa": "Creative",
    "1IbAlrM5on9JnqMQauZ66Mc2cNkG-iw_z": "Promotions", 
    "13KfznyCUUB_QW4Vz8sO68ll658aKoL5J": "Company Wide Resources",
    "16_DkfrgX7hw9AfzfG4O5jB4lSjBDcMl4": "Trainings/How To",
    "1OvkwfqSspepXB43rlwz1aL6QTLdbuAl3": "Media Center",  # This might be missing from ChromaDB
    "1XV-uj4yti8Cw-EN_t8Kpma9NaJPGQJZ2": "Engineering",
    "19lBrZ5PKAdyaZeBBgvCkmJNyzjhC3dFO": "Production"
}

def main():
    print("Creating indexed_folders.json from known folder mapping...")
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path='./chroma_db',
        settings=Settings(allow_reset=True)
    )
    
    # Get all collections that start with "folder_"
    collections = client.list_collections()
    folder_collections = [col for col in collections if col.name.startswith('folder_')]
    
    print(f"Found {len(folder_collections)} folder collections in ChromaDB")
    
    indexed_folders = {}
    
    for col in folder_collections:
        # Extract folder ID from collection name (remove "folder_" prefix)
        folder_id = col.name[7:]  # Remove "folder_" prefix
        
        # Get folder name from our mapping
        folder_name = FOLDER_MAPPING.get(folder_id, f"Unknown Folder ({folder_id[:8]}...)")
        
        print(f"Processing {col.name} -> '{folder_name}' ({col.count()} items)")
        
        # Add to indexed_folders structure
        indexed_folders[folder_id] = {
            "name": folder_name,
            "collection_name": col.name,  # Use the actual ChromaDB collection name 
            "indexed_at": datetime.now().isoformat(),
            "files_processed": col.count(),
            "location": "Google Drive"
        }
    
    # Write the indexed_folders.json file
    with open('indexed_folders.json', 'w', encoding='utf-8') as f:
        json.dump(indexed_folders, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Created indexed_folders.json with {len(indexed_folders)} folders")
    print("Collections registered:")
    for folder_id, info in indexed_folders.items():
        print(f"  - {info['name']}: {info['files_processed']} files (collection: {info['collection_name']})")
    
    print("\n🚀 The main RAG system should now detect your collections!")
    print("Please restart your Flask server for the changes to take effect.")

if __name__ == "__main__":
    main()