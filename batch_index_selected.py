#!/usr/bin/env python3
"""
Batch indexer for selected folders (excluding Market Resources)
"""

import subprocess
import sys
import time

# All folders except Market Resources
folders_to_index = [
    ("Admin/Traffic", "1uEfnwP1zKT2D-E5F854qU38pt35vGysR"),
    ("Sports", "17tKM1qfm2xL3AX-DZStoR6aKZI62mUbb"),
    ("Sales", "1pavO4fb0UC3M9wvTmO_Ha4XEpc41fqy2"),
    ("Human Resources", "1I60lMExM4aWG9GeLwqlj0KbZp8B-DqcF"),
    ("Digital", "1xMZjA6iuAy3sScRpkrh2Q4Ss4MEstd6l"),
    ("Programming", "1T2UYUSHd4aX_F-_fBkTN0IyoXwYz3K2G"),
    ("Creative", "1ST8F13mAslBww8Gc3xatK2jr8Y3ExhCx"),
    ("Promotions", "1IbAlrM5on9JnqMQauZ66Mc2cNkG-8dcW"),
    ("Company Wide Resources", "13KfznyCUUB_QW4Vz8sO68ll658aKvw7G"),
    ("Trainings/How To", "16_DkfrgX7hw9AfzfG4O5jB4lSjBDBvkF"),
    ("Media Center", "1OvkwfqSspepXB43rlwz1aL6QTLdbA2qZ"),
    ("Engineering", "1XV-uj4yti8Cw-EN_t8Kpma9NaJPGKH4f"),
    ("Production", "19lBrZ5PKAdyaZeBBgvCkmJNyzjhCKqbr")
]

def index_folder(folder_name, folder_id):
    """Index a single folder"""
    print(f"\n" + "="*80)
    print(f"🔄 Starting indexing: {folder_name}")
    print(f"📁 Folder ID: {folder_id}")
    print("="*80)
    
    try:
        # Run the indexer for this specific folder
        result = subprocess.run([
            sys.executable, "console_indexer_fixed.py", 
            "--index-folder", folder_id
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully indexed: {folder_name}")
            return True
        else:
            print(f"❌ Failed to index: {folder_name} (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error indexing {folder_name}: {str(e)}")
        return False

def main():
    print("🚀 Batch Indexing Selected Folders (Excluding Market Resources)")
    print(f"📊 Total folders to index: {len(folders_to_index)}")
    
    successful = []
    failed = []
    
    for i, (folder_name, folder_id) in enumerate(folders_to_index, 1):
        print(f"\n📋 Progress: {i}/{len(folders_to_index)}")
        
        if index_folder(folder_name, folder_id):
            successful.append(folder_name)
        else:
            failed.append(folder_name)
            
        # Small delay between folders
        if i < len(folders_to_index):
            print("⏸️  Waiting 3 seconds before next folder...")
            time.sleep(3)
    
    # Summary
    print("\n" + "="*80)
    print("📊 INDEXING COMPLETE - SUMMARY")
    print("="*80)
    print(f"✅ Successfully indexed: {len(successful)} folders")
    for folder in successful:
        print(f"   ✓ {folder}")
    
    if failed:
        print(f"\n❌ Failed to index: {len(failed)} folders")
        for folder in failed:
            print(f"   ✗ {folder}")
    else:
        print("\n🎉 All folders indexed successfully!")
    
    print(f"\n📈 Total: {len(successful)}/{len(folders_to_index)} folders completed")

if __name__ == "__main__":
    main()