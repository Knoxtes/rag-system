#!/usr/bin/env python3

"""
Create indexed_folders.json from ChromaDB collections
"""

import chromadb
from chromadb.config import Settings
import json
from google_drive_oauth import get_drive_service
from datetime import datetime
import time

def get_folder_name(drive_service, folder_id):
    """Get folder name from Google Drive API"""
    try:
        file = drive_service.files().get(fileId=folder_id).execute()
        return file['name']
    except Exception as e:
        print(f"Error getting folder name for {folder_id}: {e}")
        return f"Unknown Folder ({folder_id[:8]}...)"

def main():
    print("Creating indexed_folders.json from ChromaDB collections...")
    
    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path='./chroma_db',
        settings=Settings(allow_reset=True)
    )
    
    # Get Google Drive service
    print("Authenticating with Google Drive...")
    drive_service = get_drive_service()
    
    # Get all collections that start with "folder_"
    collections = client.list_collections()
    folder_collections = [col for col in collections if col.name.startswith('folder_')]
    
    print(f"Found {len(folder_collections)} folder collections")
    
    indexed_folders = {}
    
    for col in folder_collections:
        # Extract folder ID from collection name (remove "folder_" prefix)
        folder_id = col.name[7:]  # Remove "folder_" prefix
        
        print(f"Processing {col.name} (ID: {folder_id}) with {col.count()} items...")
        
        # Get folder name from Google Drive
        folder_name = get_folder_name(drive_service, folder_id)
        
        # Create collection name from folder name (clean it for ChromaDB)
        collection_name = folder_name.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Add to indexed_folders structure
        indexed_folders[folder_id] = {
            "name": folder_name,
            "collection_name": col.name,  # Use the actual ChromaDB collection name
            "indexed_at": datetime.now().isoformat(),
            "files_processed": col.count(),
            "location": "Google Drive"
        }
        
        print(f"  → {folder_name} ({col.count()} files)")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Write the indexed_folders.json file
    with open('indexed_folders.json', 'w', encoding='utf-8') as f:
        json.dump(indexed_folders, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Created indexed_folders.json with {len(indexed_folders)} folders")
    print("The main RAG system should now be able to detect your collections!")

if __name__ == "__main__":
    main()