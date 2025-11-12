#!/usr/bin/env python3
"""
Test Incremental Indexing System
Demonstrates how the incremental indexing works and its benefits
"""

import os
import json
import time
from incremental_indexing import IncrementalIndexingManager

def test_incremental_indexing():
    """Test the incremental indexing functionality"""
    
    print("🧪 INCREMENTAL INDEXING TEST")
    print("=" * 60)
    
    # Initialize manager
    test_tracking_file = "test_file_tracking.json"
    manager = IncrementalIndexingManager(tracking_file=test_tracking_file)
    
    print("✅ Incremental indexing manager initialized")
    
    # Test scenario 1: All new files
    print("\n📋 Scenario 1: All New Files")
    print("-" * 60)
    
    test_files = [
        {
            'id': 'file1_pdf',
            'name': 'company_policy.pdf',
            'modifiedTime': '2025-11-07T10:00:00Z',
            'size': '1024',
            'mimeType': 'application/pdf'
        },
        {
            'id': 'file2_img',
            'name': 'org_chart.png',
            'modifiedTime': '2025-11-07T10:30:00Z',
            'size': '2048',
            'mimeType': 'image/png'
        },
        {
            'id': 'file3_doc',
            'name': 'meeting_notes.docx',
            'modifiedTime': '2025-11-07T11:00:00Z',
            'size': '4096',
            'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    ]
    
    categorized = manager.filter_files_for_processing(test_files, "test_collection")
    print(manager.get_incremental_summary(categorized))
    
    # Mark files as processed
    for file in test_files:
        file_info = dict(file)
        file_info['collection_name'] = 'test_collection'
        file_info['chunks_created'] = 5
        manager.mark_file_processed(file['id'], file_info)
    
    print("✅ Files marked as processed")
    
    # Test scenario 2: One file modified, others unchanged
    print("\n📋 Scenario 2: One File Modified")
    print("-" * 60)
    
    # Modify one file
    test_files[1]['modifiedTime'] = '2025-11-07T15:30:00Z'  # Updated timestamp
    test_files[1]['size'] = '2560'  # Updated size
    
    categorized = manager.filter_files_for_processing(test_files, "test_collection")
    print(manager.get_incremental_summary(categorized))
    
    # Test scenario 3: Add new file to existing collection
    print("\n📋 Scenario 3: Add New File")
    print("-" * 60)
    
    test_files.append({
        'id': 'file4_new',
        'name': 'quarterly_report.xlsx',
        'modifiedTime': '2025-11-07T16:00:00Z',
        'size': '8192',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    
    categorized = manager.filter_files_for_processing(test_files, "test_collection")
    print(manager.get_incremental_summary(categorized))
    
    # Test scenario 4: All files up to date
    print("\n📋 Scenario 4: All Files Up to Date")
    print("-" * 60)
    
    # Mark the new file as processed
    file_info = dict(test_files[-1])
    file_info['collection_name'] = 'test_collection'
    file_info['chunks_created'] = 8
    manager.mark_file_processed(test_files[-1]['id'], file_info)
    
    # Reset the modified file to original state
    test_files[1]['modifiedTime'] = '2025-11-07T10:30:00Z'
    test_files[1]['size'] = '2048'
    
    categorized = manager.filter_files_for_processing(test_files, "test_collection")
    print(manager.get_incremental_summary(categorized))
    
    # Test file tracking functionality
    print("\n📋 File Tracking Information")
    print("-" * 60)
    
    tracked_files = manager.get_collection_files("test_collection")
    print(f"📁 Collection 'test_collection' tracks {len(tracked_files)} files:")
    
    for file_id in tracked_files:
        file_info = manager.file_registry[file_id]
        print(f"  📄 {file_info['file_name']}")
        print(f"     Last indexed: {file_info['last_indexed']}")
        print(f"     Chunks: {file_info['chunks_created']}")
        print(f"     Modified: {file_info['modified_time']}")
    
    # Demonstrate performance benefits
    print("\n📊 Performance Benefits")
    print("-" * 60)
    
    total_files = len(test_files)
    unchanged_files = len(categorized['unchanged'])
    
    print(f"Total files in folder: {total_files}")
    print(f"Files that would be skipped: {unchanged_files}")
    print(f"Efficiency gain: {unchanged_files/total_files*100:.1f}%")
    print(f"Time savings: ~{unchanged_files * 2:.0f} minutes (estimated)")
    
    # Save tracking state
    manager.save_file_registry()
    print(f"\n✅ File tracking saved to: {test_tracking_file}")
    
    print("\n🎯 Key Benefits of Incremental Indexing:")
    print("  ✅ Only processes changed files")
    print("  ✅ Automatically detects new files") 
    print("  ✅ Removes deleted files from index")
    print("  ✅ Tracks modification timestamps")
    print("  ✅ Maintains collection integrity")
    print("  ✅ Dramatically reduces re-indexing time")
    
    # Cleanup
    if os.path.exists(test_tracking_file):
        os.remove(test_tracking_file)
        print(f"\n🧹 Cleaned up test file: {test_tracking_file}")
    
    print("\n🎉 Incremental indexing test complete!")


def demonstrate_real_world_scenario():
    """Show how incremental indexing would work in practice"""
    
    print("\n\n🌍 REAL-WORLD USAGE SCENARIO")
    print("=" * 60)
    
    print("📋 Typical workflow:")
    print("1. 🏢 Company has 500 documents in Google Drive folder")
    print("2. 🚀 Initial indexing: processes all 500 files (~16 hours)")
    print("3. 📅 Next week: only 15 files were modified/added")
    print("4. ⚡ Incremental indexing: processes only 15 files (~30 minutes)")
    print("5. 🎯 Result: 97% time savings!")
    
    print("\n📊 Time Comparison:")
    print("Without incremental indexing:")
    print("  - Week 1: 16 hours")
    print("  - Week 2: 16 hours (full re-index)")
    print("  - Week 3: 16 hours (full re-index)")
    print("  - Total: 48 hours")
    
    print("\nWith incremental indexing:")
    print("  - Week 1: 16 hours (initial)")
    print("  - Week 2: 30 minutes (incremental)")
    print("  - Week 3: 30 minutes (incremental)")
    print("  - Total: 17 hours")
    
    print("\n🎉 Time saved: 31 hours (65% reduction)")
    
    print("\n✨ Additional Benefits:")
    print("  🔄 Automatic cleanup of deleted files")
    print("  📝 Detailed tracking of what was processed")
    print("  🛡️  Reliability: no risk of missing files")
    print("  💡 Smart: only processes what actually changed")
    print("  🔍 Transparent: shows exactly what will be processed")


if __name__ == "__main__":
    test_incremental_indexing()
    demonstrate_real_world_scenario()