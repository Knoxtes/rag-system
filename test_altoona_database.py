"""
Simple test to see what Altoona CSV data is actually in the database
"""

import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR')

print("="*80)
print("Searching for Altoona CSV chunks...")
print("="*80)

# Search for Altoona
results = collection.query(
    query_texts=["January 2025 sales total Altoona market"],
    n_results=20,
    include=['metadatas', 'documents']
)

print(f"\nFound {len(results['ids'][0])} results\n")

# Analyze each result
altoona_csvs = {}

for i, (doc_id, metadata, document) in enumerate(zip(results['ids'][0], results['metadatas'][0], results['documents'][0]), 1):
    file_name = metadata.get('file_name', '')
    
    if 'altoona' in file_name.lower() and '.csv' in file_name.lower():
        file_id = metadata.get('file_id', '')
        is_csv = metadata.get('is_csv', 'NOT SET')
        chunk_idx = metadata.get('chunk_index', 0)
        total_chunks = metadata.get('total_chunks', 0)
        
        print(f"\n{i}. {file_name}")
        print(f"   File ID: {file_id}")
        print(f"   is_csv: {is_csv}")
        print(f"   Chunk: {chunk_idx}/{total_chunks}")
        
        # Check content for column headers
        if 'Jan-2025' in document:
            print(f"   ✅ Contains 'Jan-2025' column")
        elif 'Jan-2026' in document:
            print(f"   ❌ Contains 'Jan-2026' column")
        else:
            print(f"   ⚠️  No Jan column found in this chunk")
        
        # Show first 300 chars
        print(f"\n   Preview:")
        print(f"   {document[:300]}...")
        
        if file_id not in altoona_csvs:
            altoona_csvs[file_id] = {
                'name': file_name,
                'is_csv': is_csv,
                'total_chunks': total_chunks,
                'chunks_seen': set(),
                'has_jan_2025': False,
                'has_jan_2026': False
            }
        
        altoona_csvs[file_id]['chunks_seen'].add(chunk_idx)
        if 'Jan-2025' in document:
            altoona_csvs[file_id]['has_jan_2025'] = True
        if 'Jan-2026' in document:
            altoona_csvs[file_id]['has_jan_2026'] = True

print("\n" + "="*80)
print("SUMMARY OF ALTOONA CSVs:")
print("="*80)

for file_id, info in altoona_csvs.items():
    print(f"\n📄 {info['name']}")
    print(f"   File ID: {file_id}")
    print(f"   is_csv flag: {info['is_csv']}")
    print(f"   Total chunks: {info['total_chunks']}")
    print(f"   Chunks in top 20 results: {len(info['chunks_seen'])}")
    
    if info['has_jan_2025']:
        print(f"   ✅ Has Jan-2025 data")
    if info['has_jan_2026']:
        print(f"   ❌ Has Jan-2026 data (WRONG!)")
    
    # If is_csv is True, test fetching ALL chunks
    if info['is_csv']:
        print(f"\n   Testing auto-fetch (getting ALL {info['total_chunks']} chunks)...")
        all_chunks = collection.get(
            where={'file_id': file_id},
            include=['metadatas', 'documents']
        )
        print(f"   Retrieved: {len(all_chunks['ids'])} chunks")
        
        # Check if any chunk has Jan-2025 data
        jan_2025_found = False
        sample_revenue = None
        
        for doc in all_chunks['documents']:
            if 'Jan-2025' in doc and '$' in doc:
                jan_2025_found = True
                # Try to extract a revenue number
                lines = doc.split('\n')
                for line in lines[5:15]:  # Skip headers, check first few data rows
                    if 'Jan-2025' not in line and '|' in line:
                        parts = line.split('|')
                        if len(parts) > 5:
                            sample_revenue = parts[5].strip() if len(parts) > 5 else None
                            if sample_revenue and sample_revenue != '0.00':
                                break
                break
        
        if jan_2025_found:
            print(f"   ✅ ALL chunks contain Jan-2025 data")
            if sample_revenue:
                print(f"   Sample Jan-2025 value: {sample_revenue}")
        else:
            print(f"   ❌ Chunks do NOT contain Jan-2025 data!")

print("\n" + "="*80)
print("DIAGNOSIS:")
print("="*80)

if not altoona_csvs:
    print("❌ No Altoona CSVs found in search results!")
    print("   The query is not matching the right documents.")
elif all(not info['is_csv'] for info in altoona_csvs.values()):
    print("❌ Altoona CSVs found but is_csv flag is FALSE/NOT SET!")
    print("   Auto-fetch will NOT work.")
elif any(info['has_jan_2026'] for info in altoona_csvs.values()):
    print("❌ Finding wrong version of Altoona CSV (Jan-2026 instead of Jan-2025)")
    print("   Multiple versions exist in Drive.")
elif all(info['has_jan_2025'] for info in altoona_csvs.values()):
    print("✅ Correct Altoona CSV found with Jan-2025 data!")
    print("✅ is_csv flags are set correctly!")
    print("✅ Auto-fetch should be working!")
    print("\n   If answer is still wrong, the issue is in rag_system.py query logic.")
