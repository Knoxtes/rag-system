"""Quick check to see if CSV files have the is_csv flag"""

from vector_store import VectorStore

# Check Admin/Traffic collection
print("Checking Admin/Traffic collection for CSV flags...")
vs = VectorStore('Admin/Traffic')

# Get some Altoona chunks
results = vs.collection.get(
    limit=10,
    include=['metadatas']
)

print(f"\nTotal chunks in collection: {len(results['ids'])}")

# Check for CSV files
csv_count = 0
altoona_count = 0

for metadata in results['metadatas']:
    file_name = metadata.get('file_name', '')
    is_csv = metadata.get('is_csv', None)
    
    if 'altoona' in file_name.lower():
        altoona_count += 1
        print(f"\n✓ Found Altoona chunk:")
        print(f"  File: {file_name}")
        print(f"  is_csv flag: {is_csv}")
    
    if is_csv:
        csv_count += 1

print(f"\n" + "="*60)
print(f"Summary:")
print(f"  Chunks with is_csv=True: {csv_count}")
print(f"  Altoona chunks found: {altoona_count}")

if csv_count == 0:
    print("\n❌ NO CSV FLAGS FOUND!")
    print("   The database was NOT re-indexed with the new code.")
    print("\n📋 Next steps:")
    print("   1. Delete database: Remove-Item -Recurse -Force .\\chroma_db\\")
    print("   2. Re-run indexer: python folder_indexer.py")
    print("   3. Select: Admin/Traffic")
    print("   4. Choose: Full Re-indexing")
else:
    print("\n✅ CSV flags present! Auto-fetch should work.")
