#!/usr/bin/env python3
"""
Fix file counts in indexed_folders.json by querying actual ChromaDB collections
"""
import json
import chromadb

def fix_file_counts():
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Load indexed_folders.json
    with open('indexed_folders.json', 'r') as f:
        indexed_folders = json.load(f)
    
    print("Fixing file counts in indexed_folders.json...")
    print("=" * 80)
    
    for folder_id, folder_info in indexed_folders.items():
        collection_name = folder_info['collection_name']
        folder_name = folder_info['name']
        old_count = folder_info['files_processed']
        
        try:
            # Get collection
            collection = chroma_client.get_collection(name=collection_name)
            
            # Get all documents with metadata
            data = collection.get(include=['metadatas'])
            
            # Count unique files
            unique_files = set()
            for metadata in data['metadatas']:
                if metadata and 'file_name' in metadata:
                    file_name = metadata['file_name']
                    # Exclude universal files (they're shared across collections)
                    if not file_name.startswith('[UNIVERSAL]/'):
                        unique_files.add(file_name)
            
            actual_count = len(unique_files)
            
            # Update if different
            if old_count != actual_count:
                print(f"📝 {folder_name}")
                print(f"   Old count: {old_count}")
                print(f"   Actual count: {actual_count}")
                print(f"   Updating...")
                folder_info['files_processed'] = actual_count
            else:
                print(f"✓ {folder_name}: {actual_count} files (no change)")
                
        except Exception as e:
            print(f"❌ Error processing {folder_name}: {e}")
    
    # Save updated file
    print("\n" + "=" * 80)
    print("Saving updated indexed_folders.json...")
    with open('indexed_folders.json', 'w') as f:
        json.dump(indexed_folders, f, indent=2)
    
    print("✅ File counts updated successfully!")
    print("\nUpdated counts:")
    print("=" * 80)
    for folder_id, folder_info in indexed_folders.items():
        count = folder_info['files_processed']
        status = "✅" if count > 0 else "❌"
        print(f"{status} {folder_info['name']}: {count} files")

if __name__ == "__main__":
    fix_file_counts()
