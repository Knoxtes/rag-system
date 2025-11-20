from vector_store import VectorStore
import json

print("=" * 60)
print("CURRENT DATABASE STATUS")
print("=" * 60)

# Load indexed folders
with open('indexed_folders.json') as f:
    folders = json.load(f)

total_files = 0
total_docs = 0

for folder_id, info in folders.items():
    collection_name = f'folder_{folder_id}'
    vs = VectorStore(collection_name=collection_name)
    doc_count = vs.collection.count()
    
    print(f"\n{info['name']}:")
    print(f"  Files: {info['file_count']}")
    print(f"  Documents: {doc_count}")
    print(f"  Chunks/file: {doc_count / info['file_count']:.1f}")
    
    total_files += info['file_count']
    total_docs += doc_count

print("\n" + "=" * 60)
print(f"TOTALS: {len(folders)} folders, {total_files} files, {total_docs} documents")
print("=" * 60)
