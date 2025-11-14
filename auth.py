# auth.py - Google Drive authentication

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import sys
from config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


def authenticate_google_drive():
    """
    Authenticate with Google Drive API.
    First run will open browser for authorization.
    
    Raises:
        AuthenticationError: If authentication fails or credentials are missing
    """
    creds = None
    
    # Check if credentials file exists before proceeding
    if not os.path.exists(CREDENTIALS_FILE):
        error_msg = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                     GOOGLE DRIVE AUTHENTICATION ERROR                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

Missing: {CREDENTIALS_FILE}

To fix this issue:

1. Go to Google Cloud Console: https://console.cloud.google.com/apis/credentials
2. Create or select a project
3. Enable Google Drive API for your project
4. Create OAuth 2.0 Client ID credentials:
   - Application type: Desktop app
   - Name: RAG System (or any name you prefer)
5. Download the credentials JSON file
6. Save it as '{CREDENTIALS_FILE}' in the project root directory

Once you have the credentials file, run the application again.
"""
        print(error_msg, file=sys.stderr)
        raise AuthenticationError(f"{CREDENTIALS_FILE} not found")
    
    # Try to load existing token
    if os.path.exists(TOKEN_FILE):
        print("Loading saved credentials...")
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Warning: Could not load saved credentials: {e}")
            print("Will re-authenticate...")
            creds = None
    
    # Validate or refresh credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                print("Will re-authenticate...")
                creds = None
        
        # Get new credentials if needed
        if not creds:
            print("\n" + "="*79)
            print("GOOGLE DRIVE AUTHENTICATION REQUIRED")
            print("="*79)
            print("A browser window will open for authorization.")
            print("Please log in and grant access to Google Drive.")
            print("="*79 + "\n")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                error_msg = f"""
Authentication failed: {str(e)}

Common issues:
1. Invalid credentials.json file
2. OAuth consent screen not configured
3. Port already in use
4. Browser failed to open

Please check your Google Cloud Console settings and try again.
"""
                print(error_msg, file=sys.stderr)
                raise AuthenticationError(f"Failed to authenticate: {e}")
        
        # Save credentials for next time
        print("Saving credentials...")
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Warning: Could not save credentials: {e}")
            print("You may need to re-authenticate next time.")
    
    # Build and return Drive service
    try:
        print("Authentication successful!")
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        error_msg = f"""
Failed to create Google Drive service: {str(e)}

This may indicate:
1. Invalid credentials
2. Network connectivity issues
3. Google Drive API not enabled for your project

Please check your Google Cloud Console and try again.
"""
        print(error_msg, file=sys.stderr)
        raise AuthenticationError(f"Failed to create Drive service: {e}")


def test_authentication():
    """
    Test authentication by listing 5 files
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        print("\nTesting Google Drive authentication...")
        service = authenticate_google_drive()
        
        print("Attempting to list files from your Google Drive...")
        results = service.files().list(
            pageSize=5, 
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            print('\n✓ Authentication successful!')
            print('No files found in your Google Drive.')
        else:
            print('\n✓ Authentication successful!')
            print('\nFirst 5 files in your Drive:')
            for file in files:
                print(f"  • {file['name']}")
        
        return True
    except AuthenticationError as e:
        print(f"\n✗ Authentication failed: {e}")
        print("\nPlease follow the instructions above to fix the issue.")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during authentication: {e}")
        print("\nPlease check your credentials and try again.")
        return False


if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)
