"""
Check Altoona CSV chunks in detail
"""
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection_name = "folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR"
collection = client.get_collection(collection_name)

# Get all documents
all_docs = collection.get()

# Find Altoona CSV chunks
altoona_chunks = []
for i, (doc_id, metadata, document) in enumerate(zip(all_docs['ids'], all_docs['metadatas'], all_docs['documents'])):
    file_name = metadata.get('file_name', '')
    if 'altoona' in file_name.lower() and '6 month sales projection' in file_name.lower():
        altoona_chunks.append({
            'id': doc_id,
            'file_id': metadata.get('file_id'),
            'chunk_index': metadata.get('chunk_index'),
            'total_chunks': metadata.get('total_chunks'),
            'has_csv_marker': '[CSV CHUNK' in document if document else False,
            'content_length': len(document) if document else 0,
            'first_line': document[:150] if document else ''
        })

print(f"Found {len(altoona_chunks)} Altoona-6 Month Sales Projection chunks\n")

# Sort by chunk index
altoona_chunks.sort(key=lambda x: x['chunk_index'])

# Show summary
if altoona_chunks:
    print(f"File ID: {altoona_chunks[0]['file_id']}")
    print(f"Total chunks (from metadata): {altoona_chunks[0]['total_chunks']}")
    print(f"Actual chunks found: {len(altoona_chunks)}")
    print(f"\nChunk details:")
    print("="*80)
    
    for i, chunk in enumerate(altoona_chunks[:10]):  # Show first 10
        print(f"\nChunk {chunk['chunk_index']}:")
        print(f"  Has CSV marker: {chunk['has_csv_marker']}")
        print(f"  Content length: {chunk['content_length']} chars")
        print(f"  First line: {chunk['first_line']}...")
    
    if len(altoona_chunks) > 10:
        print(f"\n... and {len(altoona_chunks) - 10} more chunks")
    
    # Check if all chunks have CSV markers
    chunks_with_markers = sum(1 for c in altoona_chunks if c['has_csv_marker'])
    print(f"\nChunks with [CSV CHUNK marker: {chunks_with_markers}/{len(altoona_chunks)}")
    
    # Expected from CSV with 414 rows, 50 rows per chunk = 9 chunks
    print(f"\nExpected chunks (414 rows ÷ 50): 9")
    print(f"Actual chunks found: {len(altoona_chunks)}")
    
    if len(altoona_chunks) != 9:
        print(f"\n⚠️  WARNING: Chunk count mismatch!")
        print(f"   Expected: 9 chunks")
        print(f"   Found: {len(altoona_chunks)} chunks")
        print(f"   This suggests the database was NOT re-indexed with the latest CSV chunking code!")
