from vector_store import VectorStore
import json

# Check Sports collection
vs = VectorStore(collection_name='folder_17tKM1qfm2xL3AX-DZStoR6aKZI62mUbb')
doc_count = vs.collection.count()

# Load indexed folders
with open('indexed_folders.json') as f:
    data = json.load(f)

file_count = data['17tKM1qfm2xL3AX-DZStoR6aKZI62mUbb']['file_count']

print(f"Sports Collection Analysis:")
print(f"  Files in Drive: {file_count}")
print(f"  Documents in ChromaDB: {doc_count}")
print(f"  Average chunks per file: {doc_count / file_count:.1f}")
print()
print("This is normal - documents are chunked for better RAG retrieval!")
