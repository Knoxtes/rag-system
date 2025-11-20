#!/usr/bin/env python3
"""
Simple Folder ID Extractor - Get full folder IDs for manual indexing
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

def main():
    print("🔍 Getting Full Folder IDs from Google Drive...")
    
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
            return 1
        
        folder_list = folders['files']
        
        print(f"\n📁 Found {len(folder_list)} folders:")
        print("=" * 120)
        
        # Sort folders by name for easier reading
        folder_list.sort(key=lambda x: x.get('name', '').lower())
        
        print("Commands to index all folders except Market Resources:")
        print("-" * 120)
        
        for i, folder in enumerate(folder_list, 1):
            name = folder.get('name', 'Unknown')
            folder_id = folder.get('id', 'Unknown')
            
            # Skip Market Resources
            if name == "Market Resources":
                print(f"# {i:2d}. {name:<25} - SKIPPED")
            else:
                print(f"python console_indexer.py --index-folder \"{folder_id}\"  # {name}")
        
        print("-" * 120)
        print(f"📊 Total folders: {len(folder_list)}")
        print(f"🎯 Folders to index: {len([f for f in folder_list if f.get('name') != 'Market Resources'])}")
        
        print("\n💡 Copy and paste the commands above to index folders one by one.")
        print("💡 You can run them manually to control the process and see individual results.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)