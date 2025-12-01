"""
Google Drive OAuth Integration for Flask Admin
Web-based OAuth flow that works through the browser
"""

from flask import Blueprint, request, redirect, url_for, session, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import pickle
import json

# OAuth configuration
SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Full drive access (required for shared drives)
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# Create blueprint
gdrive_oauth_bp = Blueprint('gdrive_oauth', __name__, url_prefix='/admin/gdrive')

# Allow insecure transport for development only (not needed for production HTTPS)
if os.getenv('FLASK_ENV') != 'production':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def get_flow():
    """Create OAuth flow with proper redirect URI"""
    # Read credentials to determine redirect URI
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
    
    client_config = creds_data.get('installed') or creds_data.get('web')
    redirect_uris = client_config.get('redirect_uris', [])
    
    # Use environment variable, or first redirect URI from credentials, or production default
    redirect_uri = os.getenv('GDRIVE_REDIRECT_URI') or (redirect_uris[0] if redirect_uris else 'https://ask.7mountainsmedia.com/admin/gdrive/callback')
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    return flow


def get_credentials():
    """Get existing credentials from file with robust refresh handling"""
    if not os.path.exists(TOKEN_FILE):
        print("[GDrive Auth] No token file found")
        return None
    
    try:
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
        
        # Check if valid
        if creds and creds.valid:
            print("[GDrive Auth] Credentials are valid")
            return creds
        
        # Try to refresh if expired but has refresh token
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            print("[GDrive Auth] Token expired, attempting refresh...")
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                print("[GDrive Auth] Token refreshed successfully")
                return creds
            except Exception as refresh_error:
                print(f"[GDrive Auth] Token refresh failed: {refresh_error}")
                # Don't return None immediately - the token might still work for some operations
                # or we should let the caller know to re-authenticate
                return None
        
        # No refresh token available
        if creds and creds.expired and not creds.refresh_token:
            print("[GDrive Auth] Token expired and no refresh token available - re-authentication required")
            return None
        
        print("[GDrive Auth] Credentials invalid or missing")
        return None
    except Exception as load_error:
        print(f"[GDrive Auth] Error loading credentials: {load_error}")
        return None


def save_credentials(creds):
    """Save credentials to file"""
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)


@gdrive_oauth_bp.route('/status')
def auth_status():
    """Check if Google Drive is authenticated with improved error handling"""
    try:
        creds = get_credentials()
        
        if creds:
            try:
                # Test the credentials with a quick API call with timeout
                import socket
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                try:
                    service = build('drive', 'v3', credentials=creds)
                    service.files().list(pageSize=1).execute()
                finally:
                    socket.setdefaulttimeout(original_timeout)
                
                return jsonify({
                    'authenticated': True,
                    'message': 'Google Drive connected',
                    'has_refresh_token': creds.refresh_token is not None
                })
            except Exception as e:
                error_msg = str(e)
                print(f"[GDrive Status] Credentials test failed: {error_msg}")
                
                # Check if it's a token expiration issue
                if 'expired' in error_msg.lower() or 'invalid' in error_msg.lower():
                    return jsonify({
                        'authenticated': False,
                        'message': 'Token expired - please reconnect',
                        'needs_reauth': True
                    })
                
                return jsonify({
                    'authenticated': False,
                    'message': f'Connection error: {error_msg[:100]}'
                })
        
        return jsonify({
            'authenticated': False,
            'message': 'Not authenticated - please connect Google Drive'
        })
    except Exception as e:
        print(f"[GDrive Status] Status check error: {e}")
        return jsonify({
            'authenticated': False,
            'message': 'Error checking status - please try again'
        })


@gdrive_oauth_bp.route('/authorize')
def authorize():
    """Start OAuth flow"""
    try:
        flow = get_flow()
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for verification
        session['oauth_state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        return f"""
        <html>
        <head><title>OAuth Error</title></head>
        <body style="font-family: Arial; padding: 40px; background: #0f172a; color: #e2e8f0;">
            <h1 style="color: #ef4444;">❌ OAuth Setup Error</h1>
            <p>Error: {str(e)}</p>
            <h3>Setup Instructions:</h3>
            <ol>
                <li>Go to <a href="https://console.cloud.google.com/apis/credentials?project=rag-chat-system" style="color: #3b82f6;">Google Cloud Console</a></li>
                <li>Edit your OAuth client ID: <code>632169698669-n5sttmpaes91rj6v8qe17dcqlmr0fggr</code></li>
                <li>Under "Authorized redirect URIs", add: <code>https://ask.7mountainsmedia.com/admin/gdrive/callback</code></li>
                <li>Click SAVE and wait 1-2 minutes</li>
                <li><a href="/admin/dashboard" style="color: #3b82f6;">Return to Admin Dashboard</a></li>
            </ol>
        </body>
        </html>
        """


@gdrive_oauth_bp.route('/callback')
def oauth_callback():
    """Handle OAuth callback"""
    try:
        # Verify state
        state = session.get('oauth_state')
        
        if not state:
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center; background: #0f172a; color: #e2e8f0;">
                <h1 style="color: #ef4444;">❌ Invalid Session</h1>
                <p>Please start the authorization process again.</p>
                <a href="/admin/dashboard" style="color: #3b82f6; text-decoration: none; background: #1e293b; padding: 12px 24px; border-radius: 8px; display: inline-block; margin-top: 20px;">Return to Dashboard</a>
            </body>
            </html>
            """
        
        # Get the flow again
        flow = get_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Save credentials
        credentials = flow.credentials
        save_credentials(credentials)
        
        # Clear session state
        session.pop('oauth_state', None)
        
        # Test the connection
        try:
            service = build('drive', 'v3', credentials=credentials)
            result = service.files().list(pageSize=5).execute()
            files = result.get('files', [])
            
            file_list = '<ul style="text-align: left; display: inline-block;">'
            for f in files[:5]:
                file_list += f'<li>{f.get("name")}</li>'
            file_list += '</ul>'
            
            return f"""
            <html>
            <head>
                <title>Authorization Successful</title>
                <script>
                    // Auto-redirect after 3 seconds
                    setTimeout(function() {{
                        window.location.href = '/admin/dashboard';
                    }}, 3000);
                </script>
            </head>
            <body style="font-family: Arial; padding: 40px; text-align: center; background: #0f172a; color: #e2e8f0;">
                <h1 style="color: #10b981;">✅ Authorization Successful!</h1>
                <p style="font-size: 18px; margin: 20px 0;">Google Drive is now connected</p>
                <div style="background: #1e293b; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 600px;">
                    <h3>First 5 files in your Drive:</h3>
                    {file_list}
                </div>
                <p style="color: #64748b;">Redirecting to admin dashboard in 3 seconds...</p>
                <a href="/admin/dashboard" style="color: #3b82f6; text-decoration: none; background: #1e293b; padding: 12px 24px; border-radius: 8px; display: inline-block; margin-top: 20px;">Go to Dashboard Now</a>
            </body>
            </html>
            """
            
        except Exception as e:
            return f"""
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center; background: #0f172a; color: #e2e8f0;">
                <h1 style="color: #f59e0b;">⚠️ Authorization Complete (with warning)</h1>
                <p>Credentials saved, but couldn't test connection:</p>
                <code style="background: #1e293b; padding: 10px; border-radius: 4px; display: block; margin: 20px 0;">{str(e)}</code>
                <a href="/admin/dashboard" style="color: #3b82f6; text-decoration: none; background: #1e293b; padding: 12px 24px; border-radius: 8px; display: inline-block; margin-top: 20px;">Return to Dashboard</a>
            </body>
            </html>
            """
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center; background: #0f172a; color: #e2e8f0;">
            <h1 style="color: #ef4444;">❌ Authorization Failed</h1>
            <p>Error: {str(e)}</p>
            <a href="/admin/gdrive/authorize" style="color: #3b82f6; text-decoration: none; background: #1e293b; padding: 12px 24px; border-radius: 8px; display: inline-block; margin-top: 20px;">Try Again</a>
        </body>
        </html>
        """


@gdrive_oauth_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect Google Drive (remove credentials)"""
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        
        return jsonify({
            'success': True,
            'message': 'Google Drive disconnected'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_drive_service():
    """Get authenticated Drive service for use in other modules"""
    creds = get_credentials()
    
    if not creds:
        return None
    
    try:
        return build('drive', 'v3', credentials=creds)
    except:
        return None
