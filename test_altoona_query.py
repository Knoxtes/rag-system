"""
Test actual query to see what CSV data is being retrieved
"""

from rag_system import EnhancedRAGSystem

# Initialize RAG system
rag = EnhancedRAGSystem(collection_name='folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR')

# Test query
query = "What is the January 2025 sales total for Altoona market?"

print("="*80)
print("Testing Query:", query)
print("="*80)

# Search
results = rag.hybrid_search(query, top_k=10)

print(f"\nFound {len(results)} results\n")

# Check for Altoona CSVs
altoona_files = {}
for i, result in enumerate(results, 1):
    metadata = result.get('metadata', {})
    file_name = metadata.get('file_name', '')
    
    if 'altoona' in file_name.lower() and 'csv' in file_name.lower():
        file_id = metadata.get('file_id', '')
        is_csv = metadata.get('is_csv', False)
        chunk_idx = metadata.get('chunk_index', 0)
        total_chunks = metadata.get('total_chunks', 0)
        content = result.get('text', '')
        
        if file_id not in altoona_files:
            altoona_files[file_id] = {
                'file_name': file_name,
                'is_csv': is_csv,
                'total_chunks': total_chunks,
                'chunks_found': [],
                'sample_content': content[:500]
            }
        
        altoona_files[file_id]['chunks_found'].append(chunk_idx)

print("\n" + "="*80)
print("ALTOONA CSV FILES IN RESULTS:")
print("="*80)

for file_id, info in altoona_files.items():
    print(f"\n📄 {info['file_name']}")
    print(f"   File ID: {file_id}")
    print(f"   is_csv flag: {info['is_csv']}")
    print(f"   Total chunks: {info['total_chunks']}")
    print(f"   Chunks in results: {sorted(info['chunks_found'])}")
    print(f"\n   Sample content:")
    print(f"   {info['sample_content'][:300]}")
    
    # Check if it has Jan-2025 or Jan-2026
    if 'Jan-2025' in info['sample_content']:
        print(f"\n   ✅ Has Jan-2025 column")
    elif 'Jan-2026' in info['sample_content']:
        print(f"\n   ⚠️  Has Jan-2026 column (wrong file!)")

print("\n" + "="*80)
print("TESTING CSV AUTO-FETCH:")
print("="*80)

# Now test if auto-fetch is working
response = rag.answer_question(query)

print(f"\n📝 Answer: {response['answer']}")
print(f"\n📊 Sources used: {len(response.get('sources', []))}")

# Check console output for CSV auto-fetch messages
print("\n" + "="*80)
print("Check the console output above for:")
print("  - '📊 CSV AUTO-FETCH: Found X CSV file(s)'")
print("  - '📄 [filename]'")
print("  - '✓ Retrieved: X chunks'")
print("="*80)
