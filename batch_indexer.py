#!/usr/bin/env python3
"""
Get Full Folder IDs and Index All Except Market Resources
"""

import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_drive_oauth import get_drive_service
import config

def safe_drive_call(func, max_retries=3, backoff=2, **kwargs):
    """Safely call Google Drive API with retries"""
    for attempt in range(max_retries):
        try:
            return func(**kwargs).execute()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️  Drive API error (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(backoff * (attempt + 1))
    return None

def get_full_folder_list():
    """Get complete folder list with full IDs"""
    try:
        print("📂 Connecting to Google Drive...")
        drive_service = get_drive_service()
        print("✅ Connected!")
        
        shared_drive_id = config.SHARED_DRIVE_ID
        
        # Get all folders from shared drive
        query = f"parents in '{shared_drive_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folders = safe_drive_call(
            drive_service.files().list,
            q=query,
            driveId=shared_drive_id,
            corpora='drive',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id, name, modifiedTime)"
        )
        
        if not folders or 'files' not in folders:
            print("❌ No folders found")
            return []
        
        return folders['files']
    
    except Exception as e:
        print(f"❌ Error getting folders: {e}")
        return []

def main():
    print("🔍 Getting Full Folder List...")
    folders = get_full_folder_list()
    
    if not folders:
        print("❌ Could not retrieve folder list")
        return 1
    
    print(f"\n📁 Found {len(folders)} folders:")
    print("=" * 100)
    
    # Sort folders by name for easier reading
    folders.sort(key=lambda x: x.get('name', '').lower())
    
    folders_to_index = []
    
    for i, folder in enumerate(folders, 1):
        name = folder.get('name', 'Unknown')
        folder_id = folder.get('id', 'Unknown')
        
        # Skip Market Resources
        if name == "Market Resources":
            print(f"{i:2d}. {name:<25} {folder_id} [SKIPPED]")
        else:
            print(f"{i:2d}. {name:<25} {folder_id}")
            folders_to_index.append((name, folder_id))
    
    print("=" * 100)
    print(f"📊 Total folders: {len(folders)}")
    print(f"🎯 Folders to index: {len(folders_to_index)}")
    print(f"⏭️  Skipped: Market Resources")
    
    # Ask for confirmation
    print(f"\n⚠️  About to index {len(folders_to_index)} folders:")
    for name, _ in folders_to_index:
        print(f"   • {name}")
    
    response = input(f"\nProceed with indexing? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled by user")
        return 0
    
    # Index each folder
    successful = []
    failed = []
    
    print(f"\n🚀 Starting indexing process...")
    print("=" * 100)
    
    for i, (name, folder_id) in enumerate(folders_to_index, 1):
        print(f"[{i}/{len(folders_to_index)}] 🔄 Indexing: {name}")
        
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "console_indexer.py", 
                "--index-folder", folder_id
            ], capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')  # 5 minute timeout per folder
            
            if result.returncode == 0:
                print(f"    ✅ Success!")
                successful.append(name)
            else:
                print(f"    ❌ Failed!")
                if result.stderr:
                    error_lines = result.stderr.strip().split('\n')
                    # Show last few lines of error
                    for line in error_lines[-3:]:
                        if line.strip():
                            print(f"    Error: {line}")
                failed.append(name)
        
        except subprocess.TimeoutExpired:
            print(f"    ⏰ Timeout after 5 minutes")
            failed.append(name)
        except Exception as e:
            print(f"    ❌ Exception: {e}")
            failed.append(name)
        
        # Small delay between folders
        if i < len(folders_to_index):
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 100)
    print("📊 FINAL SUMMARY")
    print("=" * 100)
    print(f"✅ Successfully indexed: {len(successful)} folders")
    for name in successful:
        print(f"   • {name}")
    
    print(f"\n❌ Failed to index: {len(failed)} folders")
    for name in failed:
        print(f"   • {name}")
    
    print(f"\n🎉 Process complete! {len(successful)}/{len(folders_to_index)} folders indexed successfully.")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)