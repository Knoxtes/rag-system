import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR')

# Get all documents and check for Altoona
print("Getting sample documents...")
results = collection.get(limit=100, include=['metadatas'])

altoona_count = 0
sample_files = set()

for metadata in results['metadatas']:
    file_name = metadata.get('file_name', '')
    sample_files.add(file_name)
    
    if 'altoona' in file_name.lower():
        altoona_count += 1
        print(f"\n✓ Found: {file_name}")
        print(f"  is_csv: {metadata.get('is_csv', 'NOT SET')}")
        print(f"  chunk: {metadata.get('chunk_index')}/{metadata.get('total_chunks')}")

print(f"\n{'='*60}")
print(f"Total Altoona files found in first 100 chunks: {altoona_count}")
print(f"\nSample of other files:")
for f in list(sample_files)[:10]:
    print(f"  - {f}")
