#!/usr/bin/env python3
"""
Batch Index All Folders (Except Market Resources)

This script will automatically index all 13 folders from Google Drive
except for "Market Resources", running them sequentially with proper
error handling and Unicode support.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Fix Windows console encoding
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Folder IDs to index (all except Market Resources and already indexed ones)
# Removed: Admin/Traffic and Sports (already indexed)
FOLDERS_TO_INDEX = [
    ("Company Wide Resources", "13KfznyCUUB_QW4Vz8sO68ll658aKoL5J"),
    ("Creative", "1ST8F13mAslBww8Gc3xatK2jr8Y3E5fOa"),
    ("Digital", "1xMZjA6iuAy3sScRpkrh2Q4Ss4MEt3x3P"),
    ("Engineering", "1XV-uj4yti8Cw-EN_t8Kpma9NaJPGQJZ2"),
    ("Human Resources", "1I60lMExM4aWG9GeLwqlj0KbZp8B-lCIl"),
    ("Media Center", "1OvkwfqSspepXB43rlwz1aL6QTLdbD8o-"),
    ("Production", "19lBrZ5PKAdyaZeBBgvCkmJNyzjhC3dFO"),
    ("Programming", "1T2UYUSHd4aX_F-_fBkTN0IyoXwYze_rw"),
    ("Promotions", "1IbAlrM5on9JnqMQauZ66Mc2cNkG-iw_z"),
    ("Sales", "1pavO4fb0UC3M9wvTmO_Ha4XEpc41JBCG"),
    ("Trainings/How To", "16_DkfrgX7hw9AfzfG4O5jB4lSjBDcMl4"),
]

def run_indexing():
    """Run indexing for all folders"""
    print("🚀 BATCH INDEXING ALL FOLDERS (EXCEPT MARKET RESOURCES)")
    print("=" * 80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Total folders to index: {len(FOLDERS_TO_INDEX)}")
    print()
    
    successful = []
    failed = []
    
    for i, (folder_name, folder_id) in enumerate(FOLDERS_TO_INDEX, 1):
        print(f"[{i}/{len(FOLDERS_TO_INDEX)}] 🔄 Indexing: {folder_name}")
        print(f"    ID: {folder_id}")
        
        try:
            # Use PYTHONIOENCODING to ensure UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Run console indexer with proper encoding
            result = subprocess.run([
                sys.executable, "console_indexer_fixed.py", 
                "--index-folder", folder_id,
                "--force"  # Use force to overwrite if collection exists
            ], 
            env=env,
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            timeout=1800  # 30 minute timeout per folder (increased for larger collections)
            )
            
            if result.returncode == 0:
                print("    ✅ SUCCESS!")
                successful.append(folder_name)
            else:
                print("    ❌ FAILED!")
                # Show stderr if available
                if result.stderr:
                    error_lines = [line.strip() for line in result.stderr.split('\n') if line.strip()]
                    # Show last few meaningful error lines
                    for line in error_lines[-3:]:
                        if 'Error' in line or 'Exception' in line or '❌' in line:
                            print(f"    └─ {line}")
                failed.append((folder_name, result.stderr.strip() if result.stderr else "Unknown error"))
        
        except subprocess.TimeoutExpired:
            print("    ⏰ TIMEOUT (30 minutes exceeded)")
            failed.append((folder_name, "Timeout after 30 minutes"))
        
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            failed.append((folder_name, str(e)))
        
        # Brief pause between folders
        if i < len(FOLDERS_TO_INDEX):
            print("    💤 Waiting 3 seconds...\n")
            time.sleep(3)
        else:
            print()
    
    # Final summary
    print("=" * 80)
    print("📊 BATCH INDEXING SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully indexed: {len(successful)} folders")
    if successful:
        for name in successful:
            print(f"   • {name}")
    
    print(f"\n❌ Failed to index: {len(failed)} folders")
    if failed:
        for name, error in failed:
            print(f"   • {name}")
            if error:
                # Show first line of error
                first_error_line = error.split('\n')[0][:100]
                print(f"     └─ {first_error_line}")
    
    print(f"\n📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Success rate: {len(successful)}/{len(FOLDERS_TO_INDEX)} ({len(successful)/len(FOLDERS_TO_INDEX)*100:.1f}%)")
    print("=" * 80)
    
    return len(failed) == 0

def main():
    try:
        print("🔍 Batch Indexer for RAG System")
        print(f"📂 Will index {len(FOLDERS_TO_INDEX)} folders (skipping Market Resources)")
        print("\nFolders to index:")
        for i, (name, folder_id) in enumerate(FOLDERS_TO_INDEX, 1):
            print(f"  {i:2d}. {name}")
        
        response = input(f"\n⚠️  Proceed with batch indexing? This may take a while. (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Cancelled by user")
            return 0
        
        print("\n🚀 Starting batch indexing process...")
        success = run_indexing()
        
        if success:
            print("\n🎉 All folders indexed successfully!")
            return 0
        else:
            print("\n⚠️  Some folders failed to index. Check the summary above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user (Ctrl+C)")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())