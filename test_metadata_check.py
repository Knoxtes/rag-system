"""
Test script to check what metadata is actually stored in the database
"""
import chromadb

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Get Admin/Traffic collection
collection_name = "folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR"
print(f"Connecting to collection: {collection_name}")

collection = client.get_collection(collection_name)
print(f"Total documents in collection: {collection.count()}")

# Get a sample of documents to see their metadata
all_docs = collection.get(limit=10)

print(f"\nFound {len(all_docs['ids'])} sample documents")
print("\n" + "="*80)

# Show metadata for first few documents
for i, (doc_id, metadata, document) in enumerate(zip(all_docs['ids'][:5], all_docs['metadatas'][:5], all_docs['documents'][:5])):
    print(f"\nDocument {i+1}:")
    print(f"  ID: {doc_id}")
    print(f"  Metadata keys: {list(metadata.keys())}")
    print(f"  File name: {metadata.get('file_name', 'N/A')}")
    print(f"  Chunk index: {metadata.get('chunk_index', 'N/A')}")
    print(f"  Total chunks: {metadata.get('total_chunks', 'N/A')}")
    print(f"  Has 'is_csv' flag: {'is_csv' in metadata}")
    if 'is_csv' in metadata:
        print(f"  is_csv value: {metadata['is_csv']}")
    
    # Show first 100 chars of content
    preview = document[:100] if document else ""
    print(f"  Content preview: {preview}...")

print("\n" + "="*80)

# Search specifically for Altoona CSV
print("\nSearching for Altoona documents...")
altoona_docs = collection.get(
    where={"file_name": {"$contains": "Altoona"}},
    limit=20
)

print(f"Found {len(altoona_docs['ids'])} Altoona documents")

if altoona_docs['ids']:
    print("\nFirst Altoona document metadata:")
    metadata = altoona_docs['metadatas'][0]
    print(f"  File name: {metadata.get('file_name')}")
    print(f"  Metadata keys: {list(metadata.keys())}")
    print(f"  Has 'is_csv': {'is_csv' in metadata}")
    
    # Show content preview
    content = altoona_docs['documents'][0][:200]
    print(f"\n  Content preview:\n{content}...")
