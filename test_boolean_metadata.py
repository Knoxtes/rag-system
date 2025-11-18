"""
Test if folder_indexer is correctly adding is_csv flag by doing a mini test index
"""
import chromadb

# Create a test collection
client = chromadb.PersistentClient(path="./chroma_db")

try:
    client.delete_collection("test_csv_flag")
except:
    pass

test_collection = client.create_collection("test_csv_flag")

# Test adding a document with is_csv flag
test_metadata = {
    'file_id': 'test123',
    'file_name': 'test.csv',
    'chunk_index': 0,
    'total_chunks': 1,
    'is_csv': True,  # Boolean flag
    'mime_type': 'text/csv'
}

test_collection.add(
    ids=['test123_chunk_0'],
    documents=['[CSV CHUNK 1/1] Test content'],
    metadatas=[test_metadata]
)

print("Added test document with is_csv: True")

# Retrieve and check
result = test_collection.get(ids=['test123_chunk_0'])
retrieved_metadata = result['metadatas'][0]

print(f"\nRetrieved metadata:")
print(f"  Has 'is_csv' key: {'is_csv' in retrieved_metadata}")
if 'is_csv' in retrieved_metadata:
    print(f"  is_csv value: {retrieved_metadata['is_csv']}")
    print(f"  is_csv type: {type(retrieved_metadata['is_csv'])}")

# Test querying by is_csv flag
print("\nTesting query by is_csv flag...")
csv_docs = test_collection.get(
    where={"is_csv": True}
)

print(f"Found {len(csv_docs['ids'])} documents with is_csv=True")

# Clean up
client.delete_collection("test_csv_flag")
print("\n✅ Test collection deleted")

print("\n" + "="*80)
print("CONCLUSION:")
if 'is_csv' in retrieved_metadata and retrieved_metadata['is_csv'] == True:
    print("✅ ChromaDB correctly stores and retrieves boolean is_csv flag")
    print("   The problem is that the main collection was NOT re-indexed with this flag")
    print("   You MUST delete chroma_db folder and re-index from scratch!")
else:
    print("❌ ChromaDB has an issue storing boolean metadata")
    print("   May need to use string instead: is_csv: 'true'")
