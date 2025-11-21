#!/usr/bin/env python3
"""
Live Output Batch Indexer for Remaining Folders

This script will show live output from each indexing operation
and allows you to see real-time progress.
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

# Folders to index (remaining ones, excluding Market Resources, already indexed, and Creative)
# Skipping Creative folder due to large size (941 files)
FOLDERS_TO_INDEX = [
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

def run_indexer_with_live_output(folder_name, folder_id):
    """Run the indexer and show live output"""
    print(f"\n{'='*80}")
    print(f"🚀 INDEXING: {folder_name}")
    print(f"📁 Folder ID: {folder_id}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        # Set up environment
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run with live output (no capture_output so we see real-time progress)
        result = subprocess.run([
            sys.executable, "console_indexer_fixed.py",
            "--index-folder", folder_id,
            "--force"
        ],
        env=env,
        text=True,
        timeout=1800  # 30 minutes
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ SUCCESS: {folder_name} indexed successfully!")
        else:
            print(f"\n❌ FAILED: {folder_name} indexing failed with exit code {result.returncode}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"\n⏰ TIMEOUT: {folder_name} exceeded 30 minutes")
        return False
    except KeyboardInterrupt:
        print(f"\n❌ INTERRUPTED: User stopped indexing of {folder_name}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: Exception while indexing {folder_name}: {e}")
        return False

def main():
    print("🎯 Live Output Batch Indexer")
    print("=" * 50)
    print("This will index all remaining folders with live progress output.")
    print("(Skipping Creative folder due to large size - 941 files)")
    print(f"Total folders to process: {len(FOLDERS_TO_INDEX)}")
    
    print("\nFolders to index:")
    for i, (name, folder_id) in enumerate(FOLDERS_TO_INDEX, 1):
        print(f"  {i:2d}. {name}")
    
    response = input(f"\n🤔 Proceed with indexing? You'll see live progress for each folder. (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled by user")
        return 0
    
    # Track results
    successful = []
    failed = []
    start_time = datetime.now()
    
    try:
        for i, (folder_name, folder_id) in enumerate(FOLDERS_TO_INDEX, 1):
            print(f"\n📊 OVERALL PROGRESS: {i}/{len(FOLDERS_TO_INDEX)} folders")
            
            if run_indexer_with_live_output(folder_name, folder_id):
                successful.append(folder_name)
            else:
                failed.append(folder_name)
                
                # Ask if user wants to continue after failure
                if i < len(FOLDERS_TO_INDEX):
                    cont = input(f"\n⚠️  Continue with remaining {len(FOLDERS_TO_INDEX) - i} folders? (y/N): ").strip().lower()
                    if cont not in ['y', 'yes']:
                        print("❌ Stopped by user after failure")
                        break
            
            # Brief pause between folders (except after last one)
            if i < len(FOLDERS_TO_INDEX):
                print("\n💤 Waiting 5 seconds before next folder...")
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n❌ Batch indexing interrupted by user")
        return 1
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"⏰ Total time: {duration}")
    print(f"✅ Successfully indexed: {len(successful)} folders")
    
    if successful:
        for name in successful:
            print(f"   • {name}")
    
    if failed:
        print(f"\n❌ Failed to index: {len(failed)} folders")
        for name in failed:
            print(f"   • {name}")
    
    success_rate = len(successful) / (len(successful) + len(failed)) * 100 if (successful or failed) else 0
    print(f"\n🎯 Success rate: {success_rate:.1f}%")
    
    if len(failed) == 0:
        print("\n🎉 All folders indexed successfully!")
        return 0
    else:
        print(f"\n⚠️  {len(failed)} folders had issues. Check output above for details.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)