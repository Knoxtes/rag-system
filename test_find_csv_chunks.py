"""
Search for documents that contain CSV chunk markers
"""
import chromadb

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Get Admin/Traffic collection
collection_name = "folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR"
print(f"Connecting to collection: {collection_name}")

collection = client.get_collection(collection_name)
print(f"Total documents in collection: {collection.count()}\n")

# Get all documents
all_docs = collection.get()

print("Searching for CSV chunk markers...")
csv_chunks = []

for i, (doc_id, metadata, document) in enumerate(zip(all_docs['ids'], all_docs['metadatas'], all_docs['documents'])):
    # Check if document contains CSV chunk marker
    if document and "[CSV CHUNK" in document:
        csv_chunks.append({
            'id': doc_id,
            'file_name': metadata.get('file_name'),
            'file_id': metadata.get('file_id'),
            'chunk_index': metadata.get('chunk_index'),
            'total_chunks': metadata.get('total_chunks'),
            'has_is_csv_flag': 'is_csv' in metadata,
            'content_preview': document[:200]
        })

print(f"Found {len(csv_chunks)} documents with CSV chunk markers\n")

# Group by file_id
csv_files = {}
for chunk in csv_chunks:
    file_id = chunk['file_id']
    if file_id not in csv_files:
        csv_files[file_id] = []
    csv_files[file_id].append(chunk)

print(f"CSV chunks grouped into {len(csv_files)} files:")
print("="*80)

for file_id, chunks in csv_files.items():
    print(f"\nFile: {chunks[0]['file_name']}")
    print(f"  File ID: {file_id}")
    print(f"  Total chunks found: {len(chunks)}")
    print(f"  Expected total chunks: {chunks[0]['total_chunks']}")
    print(f"  Has 'is_csv' flag: {chunks[0]['has_is_csv_flag']}")
    
    # Show first chunk preview
    print(f"\n  First chunk preview:")
    print(f"  {chunks[0]['content_preview']}...")

print("\n" + "="*80)

# Check for Altoona specifically
print("\nSearching for Altoona CSV...")
altoona_chunks = [c for c in csv_chunks if 'altoona' in c['file_name'].lower()]

if altoona_chunks:
    print(f"Found {len(altoona_chunks)} Altoona CSV chunks")
    print(f"File: {altoona_chunks[0]['file_name']}")
    print(f"Has 'is_csv' flag: {altoona_chunks[0]['has_is_csv_flag']}")
else:
    print("No Altoona CSV chunks found!")
    
    # Search for any file with "altoona" in name
    print("\nSearching for any files with 'altoona' in name...")
    altoona_any = [
        {'file_name': m.get('file_name'), 'has_is_csv': 'is_csv' in m}
        for m in all_docs['metadatas'] 
        if m.get('file_name') and 'altoona' in m.get('file_name').lower()
    ]
    
    if altoona_any:
        print(f"Found {len(altoona_any)} documents with 'altoona' in name:")
        for doc in altoona_any[:5]:
            print(f"  - {doc['file_name']} (has is_csv: {doc['has_is_csv']})")
    else:
        print("No files with 'altoona' in name found at all!")
