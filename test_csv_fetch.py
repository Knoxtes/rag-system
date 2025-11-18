import chromadb
from vector_store import VectorStore

# Test if we can fetch all chunks of a CSV file
client = chromadb.PersistentClient(path="./chroma_db")

# Get the collection
collection_name = "folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR"  # Admin/Traffic collection
try:
    collection = client.get_collection(collection_name)
    
    # Get all documents
    all_docs = collection.get()
    
    print(f"Total documents in collection: {len(all_docs['ids'])}")
    
    # Find CSV files
    csv_files = {}
    for i, metadata in enumerate(all_docs['metadatas']):
        if metadata.get('is_csv', False):
            file_id = metadata.get('file_id')
            file_name = metadata.get('file_name')
            chunk_index = metadata.get('chunk_index', 0)
            total_chunks = metadata.get('total_chunks', 1)
            
            if file_id not in csv_files:
                csv_files[file_id] = {
                    'file_name': file_name,
                    'chunks_found': [],
                    'total_chunks': total_chunks
                }
            csv_files[file_id]['chunks_found'].append(chunk_index)
    
    print(f"\nCSV files found: {len(csv_files)}")
    for file_id, info in csv_files.items():
        print(f"\n  {info['file_name']}")
        print(f"    File ID: {file_id}")
        print(f"    Total chunks: {info['total_chunks']}")
        print(f"    Chunks found: {len(info['chunks_found'])}")
        print(f"    Chunk indices: {sorted(info['chunks_found'])}")
        
        # Test fetching all chunks by file_id
        print(f"\n  Testing fetch by file_id...")
        try:
            file_docs = collection.get(where={"file_id": file_id})
            print(f"    ✓ Retrieved {len(file_docs['ids'])} chunks using where filter")
            
            # Check content of first chunk
            if file_docs['documents']:
                first_chunk = file_docs['documents'][0]
                print(f"    First chunk preview (first 200 chars):")
                print(f"    {first_chunk[:200]}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
