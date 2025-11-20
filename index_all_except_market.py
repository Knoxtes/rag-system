#!/usr/bin/env python3
"""
Index All Folders Except Market Resources

This script will index all 13 folders from the Google Drive except for "Market Resources".
It runs each indexing operation sequentially with progress tracking.
"""

import subprocess
import sys
from datetime import datetime

# Folder IDs from the list (excluding Market Resources)
folders_to_index = [
    ("Admin/Traffic", "1uEfnwP1zKT2D-E5F854qU38pt35v"),  # Truncated for display
    ("Sports", "17tKM1qfm2xL3AX-DZStoR6aKZI62"),
    ("Sales", "1pavO4fb0UC3M9wvTmO_Ha4XEpc41"),
    ("Human Resources", "1I60lMExM4aWG9GeLwqlj0KbZp8B-"),
    ("Digital", "1xMZjA6iuAy3sScRpkrh2Q4Ss4MEt"),
    ("Programming", "1T2UYUSHd4aX_F-_fBkTN0IyoXwYz"),
    ("Creative", "1ST8F13mAslBww8Gc3xatK2jr8Y3E"),
    ("Promotions", "1IbAlrM5on9JnqMQauZ66Mc2cNkG-"),
    ("Company Wide Resources", "13KfznyCUUB_QW4Vz8sO68ll658aK"),
    ("Trainings/How To", "16_DkfrgX7hw9AfzfG4O5jB4lSjBD"),
    ("Media Center", "1OvkwfqSspepXB43rlwz1aL6QTLdb"),
    ("Engineering", "1XV-uj4yti8Cw-EN_t8Kpma9NaJPG"),
    ("Production", "19lBrZ5PKAdyaZeBBgvCkmJNyzjhC"),
]

def main():
    print("=" * 80)
    print("🚀 Indexing All Folders (Except Market Resources)")
    print("=" * 80)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Total folders to index: {len(folders_to_index)}")
    print()
    
    successful = []
    failed = []
    
    for i, (folder_name, folder_id) in enumerate(folders_to_index, 1):
        print(f"[{i}/{len(folders_to_index)}] 🔄 Indexing: {folder_name}")
        print(f"    ID: {folder_id}")
        
        try:
            # Run the console indexer for this folder
            result = subprocess.run([
                sys.executable, "console_indexer.py", 
                "--index-folder", folder_id
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"    ✅ Success!")
                successful.append(folder_name)
            else:
                print(f"    ❌ Failed!")
                print(f"    Error: {result.stderr.strip()}")
                failed.append((folder_name, result.stderr.strip()))
        
        except Exception as e:
            print(f"    ❌ Exception: {e}")
            failed.append((folder_name, str(e)))
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 INDEXING SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {len(successful)} folders")
    if successful:
        for name in successful:
            print(f"   • {name}")
    
    print(f"❌ Failed: {len(failed)} folders")
    if failed:
        for name, error in failed:
            print(f"   • {name}: {error}")
    
    print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)