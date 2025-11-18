"""
Comprehensive verification script for CSV auto-fetch functionality

This script verifies:
1. CSV files are properly indexed with is_csv flag
2. All chunks are stored for each CSV file
3. ChromaDB can retrieve all chunks by file_id
4. Expected Altoona CSV data is present
"""
import chromadb
from pathlib import Path

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def print_success(text):
    # print(f"✅ {text}")

def print_warning(text):
    # print(f"⚠️  {text}")

def print_error(text):
    # print(f"❌ {text}")

def main():
    print_header("CSV Auto-Fetch Verification Tool")
    
    # Connect to ChromaDB
    db_path = Path("./chroma_db")
    if not db_path.exists():
        print_error("chroma_db directory not found!")
            # print("   Please run: python folder_indexer.py")
        return False
    
    client = chromadb.PersistentClient(path="./chroma_db")
    collection_name = "folder_1uEfnwP1zKT2D-E5F854qU38pt35vGysR"  # Admin/Traffic
    
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        print_error(f"Cannot access collection '{collection_name}'")
            # print(f"   Error: {e}")
        return False
    
    total_docs = collection.count()
        # print(f"📊 Total documents in collection: {total_docs:,}")
    
    if total_docs == 0:
        print_error("Collection is empty! Please re-index the database.")
        return False
    
    # Test 1: Check if is_csv metadata exists
    print_header("Test 1: Checking is_csv Metadata Flag")
    
    # Sample a few documents
    sample_docs = collection.get(limit=100)
    has_is_csv = any('is_csv' in m for m in sample_docs['metadatas'])
    
    if not has_is_csv:
        print_error("No documents have 'is_csv' metadata flag!")
            # print("   This means the database was indexed with OLD code.")
            # print("   You MUST re-index with the updated folder_indexer.py")
        return False
    
    print_success("is_csv metadata flag found in database")
    
    # Count CSV vs non-CSV documents
    csv_count = sum(1 for m in sample_docs['metadatas'] if m.get('is_csv', False))
        # print(f"   Sample: {csv_count}/{len(sample_docs['metadatas'])} documents are CSV chunks")
    
    # Test 2: Find all CSV files
    print_header("Test 2: Finding CSV Files")
    
    all_docs = collection.get()
    csv_files = {}
    
    for metadata in all_docs['metadatas']:
        if metadata.get('is_csv', False):
            file_id = metadata.get('file_id')
            file_name = metadata.get('file_name')
            
            if file_id not in csv_files:
                csv_files[file_id] = {
                    'name': file_name,
                    'chunks': [],
                    'expected_total': metadata.get('total_chunks', 0)
                }
            
            csv_files[file_id]['chunks'].append(metadata.get('chunk_index', 0))
    
    if not csv_files:
        print_error("No CSV files found with is_csv=True flag!")
            # print("   Database may not have been re-indexed properly.")
        return False
    
    print_success(f"Found {len(csv_files)} CSV files")
    
    # Test 3: Verify chunk completeness
    print_header("Test 3: Verifying Chunk Completeness")
    
    all_complete = True
    altoona_found = False
    altoona_complete = False
    
    for file_id, info in csv_files.items():
        chunks_found = len(info['chunks'])
        chunks_expected = info['expected_total']
        is_complete = chunks_found == chunks_expected
        
        # Check for Altoona specifically
        if 'altoona' in info['name'].lower() and '6 month sales projection' in info['name'].lower():
            altoona_found = True
            altoona_complete = is_complete
            
                # print(f"\n📄 {info['name']}")
                # print(f"   Expected chunks: {chunks_expected}")
                # print(f"   Found chunks: {chunks_found}")
            
            if is_complete:
                print_success("All chunks present")
            else:
                print_error(f"Missing chunks! Found {chunks_found}/{chunks_expected}")
                all_complete = False
            
            # Verify chunks are sequential
            sorted_chunks = sorted(info['chunks'])
            expected_sequence = list(range(chunks_expected))
            if sorted_chunks == expected_sequence:
                print_success("Chunks are sequential (0 to {})".format(chunks_expected - 1))
            else:
                print_warning("Chunk sequence has gaps!")
                missing = set(expected_sequence) - set(sorted_chunks)
                if missing:
                    print(f"   Missing indices: {sorted(missing)}")
    
    if not altoona_found:
        print_warning("\nAltoona-6 Month Sales Projection.csv NOT FOUND")
        print("   This file should have been indexed.")
    elif not altoona_complete:
        print_error("\nAltoona CSV is INCOMPLETE!")
        all_complete = False
    
    # Test 4: Test ChromaDB query by file_id
    print_header("Test 4: Testing ChromaDB Query by file_id")
    
    if altoona_found:
        # Find Altoona file_id
        altoona_file_id = None
        for file_id, info in csv_files.items():
            if 'altoona' in info['name'].lower() and '6 month sales projection' in info['name'].lower():
                altoona_file_id = file_id
                break
        
        if altoona_file_id:
                # print(f"Testing retrieval of Altoona CSV chunks...")
                # print(f"File ID: {altoona_file_id}")
            
            try:
                result = collection.get(where={"file_id": altoona_file_id})
                retrieved_count = len(result['ids'])
                expected_count = csv_files[altoona_file_id]['expected_total']
                
                    # print(f"   Query returned: {retrieved_count} chunks")
                    # print(f"   Expected: {expected_count} chunks")
                
                if retrieved_count == expected_count:
                    print_success("ChromaDB query retrieves all chunks correctly!")
                else:
                    print_error(f"Query mismatch! Expected {expected_count}, got {retrieved_count}")
                    all_complete = False
                
                # Check if chunks have CSV CHUNK markers
                has_markers = any('[CSV CHUNK' in doc for doc in result['documents'])
                if has_markers:
                    print_success("Chunks contain [CSV CHUNK] markers")
                else:
                    print_warning("Chunks missing [CSV CHUNK] markers")
                
            except Exception as e:
                print_error(f"Query failed: {e}")
                all_complete = False
    
    # Test 5: Verify Altoona data content
    print_header("Test 5: Verifying Altoona Data Content")
    
    if altoona_found and altoona_file_id:
        try:
            result = collection.get(where={"file_id": altoona_file_id})
            
            # Check first chunk for expected content
            if result['documents']:
                first_chunk = result['documents'][0]
                
                # Should contain 414 rows for Jan-2025 version
                if '414 rows' in first_chunk:
                    print_success("Found correct Altoona CSV (414 rows for Jan-2025)")
                else:
                    print_warning("Altoona CSV may be a different month's version")
                
                # Check for expected headers
                expected_headers = ['Sponsor', 'AccountRep', 'Station', 'RevenueType', 'Jan-2025']
                headers_found = all(header in first_chunk for header in expected_headers)
                
                if headers_found:
                    print_success("CSV headers look correct")
                else:
                    print_warning("Some expected headers not found")
                
                # Show preview
                preview = first_chunk[:200]
                    # print(f"\n   First chunk preview:")
                    # print(f"   {preview}...")
        except Exception as e:
            print_error(f"Content verification failed: {e}")
    
    # Final summary
    print_header("Verification Summary")
    
    if all_complete and altoona_found and altoona_complete:
        print_success("ALL TESTS PASSED!")
        print("\n✅ CSV auto-fetch is ready to use")
        print("   The RAG system will automatically retrieve all CSV chunks")
        print("   when any chunk from a CSV file appears in search results.")
        print("\n📋 Next steps:")
        print("   1. Start the chat system: python start_chat_system.py")
        print("   2. Test query: 'What is the January 2025 sales total for Altoona market?'")
        print("   3. Expected result: $450,866.30 (all 414 rows)")
        return True
    else:
        print_error("SOME TESTS FAILED")
        print("\n❌ Issues found:")
        if not altoona_found:
            print("   - Altoona CSV not found in database")
        if altoona_found and not altoona_complete:
            print("   - Altoona CSV has missing chunks")
        if not all_complete:
            print("   - One or more CSV files have missing chunks")
        
        print("\n🔧 Recommended action:")
        print("   1. Stop the chat system if running")
        print("   2. Run: python fix_csv_indexing.py")
        print("   3. Re-index the Admin/Traffic collection")
        print("   4. Run this verification script again")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
