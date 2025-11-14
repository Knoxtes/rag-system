# auth.py - Google Drive authentication
# Updated to use simple installed app flow with urn:ietf redirect

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import sys
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def authenticate_google_drive(interactive=True):
    """
    Authenticate with Google Drive API.
    If interactive=False, only use existing credentials and don't prompt for new ones.
    """
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        print("Loading saved credentials...")
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                if not interactive:
                    return None
                creds = None
        
        if not creds and interactive:
            print("Getting new credentials...")
            print("Opening browser for authorization...")
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"FATAL ERROR: {CREDENTIALS_FILE} not found.")
                print("Please download your OAuth client credentials from Google Cloud Console.")
                return None
            
            # Use installed app flow with manual redirect URI
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            
            # Get the authorization URL without starting a local server
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            print(f"\nPlease visit this URL to authorize Google Drive access:")
            print(f"{auth_url}")
            print("\nAfter authorization, copy the authorization code and paste it here.")
            
            # Get authorization code from user
            auth_code = input("Enter the authorization code: ").strip()
            
            # Exchange code for credentials
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            print("Saving credentials...")
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        elif not creds and not interactive:
            print("❌ No valid Google Drive credentials found.")
            print("    Run 'python auth.py' to set up Google Drive authentication.")
            return None
    
    if creds:
        print("Authentication successful!")
        return build('drive', 'v3', credentials=creds)
    else:
        return None


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
