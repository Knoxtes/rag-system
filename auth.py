# auth.py - Google Drive authentication
# --- NO CHANGES ---

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import sys
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def authenticate_google_drive():
    """
    Authenticate with Google Drive API.
    First run will open browser for authorization.
    """
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        print("Loading saved credentials...")
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Getting new credentials...")
            print("A browser window will open for authorization.")
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"FATAL ERROR: {CREDENTIALS_FILE} not found.")
                print("Please download your OAuth client credentials from Google Cloud Console.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        print("Saving credentials...")
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    print("Authentication successful!")
    return build('drive', 'v3', credentials=creds)


def test_authentication():
    """Test authentication by listing 5 files"""
    try:
        service = authenticate_google_drive()
        results = service.files().list(
            pageSize=5, 
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            print('No files found in your Google Drive.')
        else:
            print('\nFirst 5 files in your Drive:')
            for file in files:
                print(f"  - {file['name']}")
        
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


if __name__ == "__main__":
    test_authentication()
