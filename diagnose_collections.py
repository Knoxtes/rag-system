#!/usr/bin/env python3
"""
Detailed collection diagnostics - check data quality and integrity
"""

import chromadb
import json
import os
from collections import defaultdict

def diagnose_collections():
    """Detailed diagnosis of all collections"""
    
    # Initialize ChromaDB client
    chroma_path = "./chroma_db"
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Get all collections
    collections = client.list_collections()
    
    # Load indexed folders for mapping
    indexed_folders = {}
    if os.path.exists('indexed_folders.json'):
        with open('indexed_folders.json', 'r') as f:
            indexed_folders = json.load(f)
    
    # Create reverse mapping
    collection_to_folder = {}
    for folder_id, folder_info in indexed_folders.items():
        collection_name = folder_info.get('collection_name')
        if collection_name:
            collection_to_folder[collection_name] = folder_info
    
    print("\n" + "=" * 80)
    print("DETAILED COLLECTION DIAGNOSTICS")
    print("=" * 80)
    print(f"Database: {os.path.abspath(chroma_path)}")
    print(f"Total collections: {len(collections)}\n")
    
    total_issues = 0
    
    for collection in collections:
        collection_name = collection.name
        folder_info = collection_to_folder.get(collection_name, {})
        folder_name = folder_info.get('name', 'Unknown')
        location = folder_info.get('location', 'Unknown')
        files_processed = folder_info.get('files_processed', 0)
        indexed_at = folder_info.get('indexed_at', 'Unknown')
        
        print("=" * 80)
        print(f"COLLECTION: {folder_name}")
        print("=" * 80)
        print(f"Location: {location}")
        print(f"Collection ID: {collection_name}")
        print(f"Expected files: {files_processed}")
        print(f"Indexed at: {indexed_at}")
        
        # Get collection data
        try:
            data = collection.get(include=['metadatas', 'documents'])
            chunk_count = len(data['ids'])
            
            print(f"\n📊 ACTUAL DATA:")
            print(f"  Total chunks: {chunk_count}")
            
            if chunk_count == 0:
                print(f"  ❌ ISSUE: Collection is empty!")
                print(f"     Expected {files_processed} files but found 0 chunks")
                total_issues += 1
                print()
                continue
            
            # Analyze metadata
            metadatas = data['metadatas']
            documents = data['documents']
            
            # Count unique files
            unique_files = set()
            file_chunks = defaultdict(int)
            mime_types = defaultdict(int)
            empty_chunks = 0
            csv_chunks = 0
            universal_files = set()
            
            for i, metadata in enumerate(metadatas):
                file_id = metadata.get('file_id', 'unknown')
                unique_files.add(file_id)
                file_chunks[file_id] += 1
                
                mime_type = metadata.get('mime_type', 'unknown')
                mime_types[mime_type] += 1
                
                # Check for CSV
                if metadata.get('is_csv', False):
                    csv_chunks += 1
                
                # Check for universal files
                file_path = metadata.get('file_path', '')
                if file_path.startswith('[UNIVERSAL]'):
                    universal_files.add(file_id)
                
                # Check for empty documents
                doc = documents[i] if i < len(documents) else ''
                if not doc or len(doc.strip()) < 50:
                    empty_chunks += 1
            
            print(f"  Unique files: {len(unique_files)}")
            print(f"  Universal files: {len(universal_files)}")
            print(f"  Specific files: {len(unique_files) - len(universal_files)}")
            
            # Check if file count matches expected
            if files_processed > 0 and len(unique_files) != files_processed:
                print(f"  ⚠️  WARNING: Expected {files_processed} files, found {len(unique_files)}")
                total_issues += 1
            
            print(f"\n📄 FILE TYPES:")
            for mime_type, count in sorted(mime_types.items(), key=lambda x: x[1], reverse=True):
                # Simplify mime type names
                simple_type = mime_type.split('/')[-1]
                if 'google-apps' in mime_type:
                    simple_type = mime_type.split('.')[-1]
                print(f"  {simple_type}: {count} chunks")
            
            print(f"\n📈 DATA QUALITY:")
            print(f"  Empty/short chunks: {empty_chunks}")
            if empty_chunks > chunk_count * 0.1:  # More than 10% empty
                print(f"  ⚠️  WARNING: High percentage of empty chunks ({empty_chunks/chunk_count*100:.1f}%)")
                total_issues += 1
            
            print(f"  CSV chunks: {csv_chunks}")
            
            # Check for files with too few chunks
            suspicious_files = []
            for file_id, chunks in file_chunks.items():
                if chunks == 1:
                    # Single chunk files - check if they're CSV or actually small
                    meta = next((m for m in metadatas if m.get('file_id') == file_id), {})
                    if not meta.get('is_csv', False):
                        # Non-CSV with single chunk might be suspicious
                        suspicious_files.append((file_id, chunks, meta.get('file_name', 'unknown')))
            
            if suspicious_files:
                print(f"\n⚠️  Suspicious files (single chunk, not CSV): {len(suspicious_files)}")
                for file_id, chunks, name in suspicious_files[:5]:  # Show first 5
                    print(f"    - {name}")
                if len(suspicious_files) > 5:
                    print(f"    ... and {len(suspicious_files) - 5} more")
            
            # Sample some documents to check quality
            print(f"\n📝 SAMPLE DOCUMENTS:")
            sample_size = min(3, len(documents))
            for i in range(sample_size):
                doc = documents[i]
                meta = metadatas[i]
                file_name = meta.get('file_name', 'unknown')
                doc_preview = doc[:100].replace('\n', ' ') if doc else '(empty)'
                print(f"  {i+1}. {file_name}")
                print(f"     Preview: {doc_preview}...")
                print(f"     Length: {len(doc)} chars")
            
            print()
            
        except Exception as e:
            print(f"\n❌ ERROR analyzing collection: {e}")
            total_issues += 1
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    populated = [c for c in collections if c.count() > 0]
    empty = [c for c in collections if c.count() == 0]
    
    print(f"✅ Populated collections: {len(populated)}")
    print(f"❌ Empty collections: {len(empty)}")
    print(f"⚠️  Issues detected: {total_issues}")
    
    if total_issues > 0:
        print(f"\n⚠️  RECOMMENDATIONS:")
        print(f"  1. Re-run indexer for empty collections")
        print(f"  2. Check collections with file count mismatches")
        print(f"  3. Investigate collections with high empty chunk percentage")
    
    print("=" * 80)
    
    return {
        'populated': len(populated),
        'empty': len(empty),
        'issues': total_issues
    }

if __name__ == "__main__":
    try:
        diagnose_collections()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
