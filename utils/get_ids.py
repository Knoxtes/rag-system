import sys
import os
sys.path.append('.')
from google_drive_oauth import get_drive_service
import config

try:
    service = get_drive_service()
    query = f"parents in '{config.SHARED_DRIVE_ID}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folders = service.files().list(
        q=query,
        driveId=config.SHARED_DRIVE_ID,
        corpora='drive',
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields='files(id, name)'
    ).execute()
    
    print("Folder IDs:")
    for folder in sorted(folders['files'], key=lambda x: x['name']):
        if folder['name'] != 'Market Resources':
            print(f"{folder['name']}: {folder['id']}")
            
except Exception as e:
    print(f"Error: {e}")