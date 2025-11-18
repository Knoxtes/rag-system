import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR')

results = collection.get(
    where={'file_name': 'Altoona-6 Month Sales Projection.csv'},
    limit=20,
    include=['metadatas', 'documents']
)

print(f"Found {len(results['ids'])} Altoona CSV versions")
print("="*80)

# Group by file path to see which months they're from
by_path = {}
for meta, doc in zip(results['metadatas'], results['documents']):
    path = meta.get('file_path', 'unknown')
    total_chunks = meta.get('total_chunks', 0)
    
    if path not in by_path:
        by_path[path] = {
            'chunks': total_chunks,
            'has_jan_2025': 'Jan-2025' in doc,
            'has_jan_2026': 'Jan-2026' in doc,
            'size': len(doc),
            'sample': doc[:400]
        }

print(f"Found {len(by_path)} different versions by path:\n")

for i, (path, info) in enumerate(by_path.items(), 1):
    print(f"{i}. Path: {path}")
    print(f"   Total chunks: {info['chunks']}")
    print(f"   Document size: {info['size']:,} chars")
    
    if info['has_jan_2025']:
        print(f"   ✅ Contains Jan-2025 data (CORRECT!)")
    if info['has_jan_2026']:
        print(f"   ❌ Contains Jan-2026 data (WRONG!)")
    
    print(f"   Preview: {info['sample'][:200]}...")
    print()

print("="*80)
print("STATUS:")
if all(info['chunks'] == 1 for info in by_path.values()):
    print("✅ All CSVs are stored as SINGLE chunks (new approach working!)")
else:
    print("❌ Some CSVs still have multiple chunks (old approach)")

if any(info['has_jan_2025'] for info in by_path.values()):
    print("✅ At least one version has Jan-2025 data")
    print("\n   But the query is finding a DIFFERENT version.")
    print("   Problem: Multiple files with same name in different folders.")
else:
    print("❌ No version with Jan-2025 data found!")
