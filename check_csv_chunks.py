import chromadb

# Connect to ChromaDB
client = chromadb.PersistentClient(path='./chroma_db')

# Get the main collection
c = client.get_collection('folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR')
docs = c.get(include=['documents', 'metadatas'])

print("Searching for Altoona CSV chunks...\n")

# Filter for Altoona CSV
altoona_chunks = []
for i, meta in enumerate(docs['metadatas']):
    if meta and meta.get('file_name') == 'Altoona-6 Month Sales Projection.csv':
        altoona_chunks.append({
            'index': i,
            'file_name': meta.get('file_name'),
            'source': meta.get('source', 'No source'),
            'chunk_index': meta.get('chunk_index', 0),
            'file_id': meta.get('file_id', 'No ID'),
            'content': docs['documents'][i]
        })

print(f"✅ Found {len(altoona_chunks)} chunks for 'Altoona-6 Month Sales Projection.csv'\n")

# Show first chunk fully
if altoona_chunks:
    first = altoona_chunks[0]
    print(f"{'='*80}")
    print(f"FIRST CHUNK FULL CONTENT")
    print(f"File: {first['file_name']}")
    print(f"Source: {first['source']}")
    print(f"Chunk index: {first['chunk_index']}")
    print(f"File ID: {first['file_id']}")
    print(f"Length: {len(first['content'])} chars")
    print(f"{'='*80}")
    print(first['content'])
    print(f"\n{'='*80}\n")
    
    # Count January entries with values
    lines = first['content'].split('\n')
    january_entries = [line for line in lines if 'january' in line.lower() or 'JANUARY' in line.lower()]
    non_zero = [line for line in january_entries if '$' in line and ('$0' not in line and '$0.00' not in line)]
    
    print(f"January 2025 entries in first chunk: {len(january_entries)}")
    print(f"Non-zero January entries: {len(non_zero)}")
    if non_zero:
        print("\nNon-zero entries:")
        for line in non_zero[:10]:
            print(f"  {line.strip()}")
