"""
Google Drive Authentication - Clean Implementation
Uses OAuth 2.0 Desktop App flow with proper error handling
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'


def authenticate_google_drive():
    """
    Authenticate with Google Drive API.
    Returns: Google Drive service object or None
    """
    creds = None
    
    # Step 1: Load existing credentials
    if os.path.exists(TOKEN_FILE):
        print("📂 Loading saved credentials...")
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
            print("✓ Credentials loaded")
        except Exception as e:
            print(f"⚠️  Failed to load credentials: {e}")
            creds = None
    
    # Step 2: Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✓ Credentials refreshed successfully")
                
                # Save refreshed credentials
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                    
            except Exception as e:
                print(f"❌ Refresh failed: {e}")
                print("   Will request new authorization")
                creds = None
        
        # Get new credentials if refresh failed or no existing creds
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print("\n" + "="*80)
                print("❌ ERROR: credentials.json not found")
                print("="*80)
                print("\nPlease create OAuth 2.0 credentials:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
                print("3. Application type: 'Desktop app'")
                print("4. Name: 'RAG System Desktop'")
                print("5. Click 'CREATE'")
                print("6. Download JSON and save as 'credentials.json' in this folder")
                print("="*80)
                return None
            
            print("\n" + "="*80)
            print("🔐 NEW AUTHORIZATION REQUIRED")
            print("="*80)
            print("\nThis will:")
            print("1. Open your browser")
            print("2. Ask you to sign in to Google")
            print("3. Request permission to access Google Drive")
            print("4. Redirect back automatically")
            print("\nPress Ctrl+C to cancel, or press Enter to continue...")
            print("="*80)
            
            try:
                input()
            except KeyboardInterrupt:
                print("\n\nCancelled by user")
                return None
            
            try:
                # Create flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, 
                    SCOPES
                )
                
                # Run local server (this opens browser automatically)
                print("\n🌐 Opening browser for authorization...")
                print("   If browser doesn't open, copy the URL that appears")
                
                creds = flow.run_local_server(
                    port=0,  # Use any available port
                    success_message='✅ Authorization successful! You can close this window.',
                    open_browser=True
                )
                
                print("\n✅ Authorization successful!")
                
                # Save credentials
                print("💾 Saving credentials...")
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                print("✓ Credentials saved")
                
            except Exception as e:
                print(f"\n❌ Authorization failed: {e}")
                print("\nTroubleshooting:")
                print("- Make sure you created a 'Desktop app' OAuth client")
                print("- Not a 'Web application' or 'Android' client")
                print("- Download the JSON and save as credentials.json")
                return None
    
    # Step 3: Build and test service
    try:
        print("🔌 Connecting to Google Drive API...")
        service = build('drive', 'v3', credentials=creds)
        
        # Quick test
        service.files().list(pageSize=1).execute()
        print("✅ Connected successfully!\n")
        
        return service
        
    except HttpError as e:
        print(f"❌ API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def test_authentication():
    """Test authentication and list some files"""
    print("\n" + "="*80)
    print("GOOGLE DRIVE AUTHENTICATION TEST")
    print("="*80 + "\n")
    
    service = authenticate_google_drive()
    
    if not service:
        print("\n❌ Authentication failed")
        return False
    
    # List first 5 files
    print("="*80)
    print("📁 First 5 files in your Google Drive:")
    print("="*80)
    
    try:
        results = service.files().list(
            pageSize=5,
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("(No files found)")
        else:
            for i, file in enumerate(files, 1):
                print(f"{i}. {file['name']}")
                print(f"   Type: {file.get('mimeType', 'Unknown')}")
                print(f"   ID: {file['id']}\n")
        
        print("="*80)
        print("✅ Authentication test passed!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_authentication()
