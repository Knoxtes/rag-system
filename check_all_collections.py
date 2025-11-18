"""Check all collections for CSV flags"""

import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()

print(f"Found {len(collections)} collections\n")
print("="*80)

total_csv_flags = 0
total_chunks = 0

for collection in collections:
    print(f"\n📁 Collection: {collection.name}")
    
    # Get a sample of documents
    try:
        results = collection.get(limit=20, include=['metadatas'])
        total_chunks += len(results['ids'])
        
        print(f"   Total chunks: {len(results['ids'])}")
        
        # Check for CSV flags
        csv_count = 0
        sample_files = set()
        
        for metadata in results['metadatas']:
            file_name = metadata.get('file_name', 'unknown')
            is_csv = metadata.get('is_csv', None)
            sample_files.add(file_name)
            
            if is_csv:
                csv_count += 1
                total_csv_flags += 1
        
        print(f"   Chunks with is_csv flag: {csv_count}")
        print(f"   Sample files (first 3):")
        for i, fname in enumerate(list(sample_files)[:3], 1):
            print(f"     {i}. {fname}")
            
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*80)
print(f"\n📊 SUMMARY:")
print(f"   Total collections: {len(collections)}")
print(f"   Total chunks checked: {total_chunks}")
print(f"   Chunks with is_csv flag: {total_csv_flags}")

if total_csv_flags == 0:
    print("\n❌ NO CSV FLAGS FOUND IN ANY COLLECTION!")
    print("\n   This means the re-indexing did NOT use the updated code.")
    print("\n   📋 Solution:")
    print("   1. Delete database: Remove-Item -Recurse -Force .\\chroma_db\\")
    print("   2. Re-run indexer: python folder_indexer.py")
    print("   3. Make sure to index the folder containing CSV files")
else:
    print(f"\n✅ Found {total_csv_flags} CSV chunks!")
    print("   CSV auto-fetch should be working.")
