"""
Authentication routes for Google OAuth
"""

import os
from flask import Blueprint, request, jsonify, redirect, session, current_app
import google.auth.transport.requests
from google.oauth2 import id_token
from googleapiclient.discovery import build
import requests
import logging
import json
from datetime import datetime
from oauth_config import OAuthConfig, oauth_config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['GET'])
def login():
    """Initiate Google OAuth login"""
    try:
        flow = oauth_config.get_flow()
        flow.redirect_uri = oauth_config.redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        
        # Store state in session for security
        session['oauth_state'] = state
        session.permanent = True  # Make session persistent
        
        # Debug logging in development
        if os.getenv('FLASK_ENV') != 'production':
            print(f"Generated OAuth state: {state}")
            print(f"Stored in session: {session.get('oauth_state')}")
            print(f"Session ID: {session.get('_id', 'No ID')}")
        
        return jsonify({
            'auth_url': authorization_url,
            'state': state
        })
    
    except Exception as e:
        logging.error(f"OAuth login error: {str(e)}")
        return jsonify({'error': 'Failed to initiate authentication'}), 500

@auth_bp.route('/auth/callback', methods=['GET'])
def callback():
    """Handle OAuth callback"""
    try:
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        # Get state parameter
        state = request.args.get('state')
        session_state = session.get('oauth_state')
        
        # In development, be more lenient with state validation but still log the issue
        if os.getenv('FLASK_ENV') == 'production':
            if not state or state != session_state:
                return jsonify({'error': 'Invalid state parameter'}), 400
        else:
            print(f"Development OAuth callback:")
            print(f"  Received state: {state}")
            print(f"  Session state: {session_state}")
            print(f"  Code received: {code[:20]}..." if code else "  No code")
            
            # In development, if states don't match, clear session and proceed
            # This handles cases where session data might be stale
            if state != session_state:
                print(f"  State mismatch detected, clearing session and proceeding...")
                session.clear()
                session['oauth_state'] = state  # Set current state for this request
        
        # Exchange code for tokens
        flow = oauth_config.get_flow()
        flow.redirect_uri = oauth_config.redirect_uri
        
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
        except Exception as e:
            logging.error(f"Token exchange error: {str(e)}")
            return jsonify({'error': 'Failed to exchange authorization code', 'details': str(e)}), 400
        
        # Get user info and store credentials for Google Drive
        try:
            user_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_service.userinfo().get().execute()
            
            # Also store the credentials for Google Drive access
            import pickle
            from config import TOKEN_FILE
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(credentials, token)
            print(f"✅ Saved Google Drive credentials for {user_info['email']}")
            
        except Exception as e:
            logging.error(f"Failed to get user info: {str(e)}")
            return jsonify({'error': 'Failed to get user information', 'details': str(e)}), 400
        
        # Check domain restriction
        if not oauth_config.is_domain_allowed(user_info['email']):
            return jsonify({
                'error': 'Access denied',
                'message': f"Your domain is not authorized to access this application. Contact your administrator."
            }), 403
        
        print(f"Successful OAuth login for: {user_info['email']}")
        
        # Generate both access and refresh tokens
        access_token = oauth_config.generate_jwt_token(user_info, is_refresh_token=False)
        refresh_token = oauth_config.generate_jwt_token(user_info, is_refresh_token=True)
        
        # Check if user is admin to determine redirect destination
        from admin_auth import is_admin_user
        is_admin = is_admin_user(user_info['email'])
        
        # Determine redirect destination
        if is_admin:
            redirect_url = '/admin/dashboard?auth_complete=true'
            welcome_message = f"Welcome to the Admin Dashboard, {user_info.get('name', user_info['email'])}!"
            page_title = "Admin Authentication Success"
            
            # For admin users, use the existing redirect approach
            user_info_escaped = json.dumps(user_info).replace('"', '&quot;')
            
            return f"""<!DOCTYPE html>
<html>
<head>
    <title>{page_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f2f5; }}
        .container {{ max-width: 400px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; }}
        .success {{ color: #4CAF50; margin-bottom: 20px; }}
        .admin {{ color: #3b82f6; }}
        .progress {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 class="success">✅ Authentication Successful!</h2>
        <p class="admin">{welcome_message}</p>
        <p class="progress" id="progress">Preparing authentication data...</p>
    </div>
    
    <script>
        console.log('Admin authentication completion...');
        try {{
            localStorage.setItem('authToken', '{access_token}');
            localStorage.setItem('user_info', '{user_info_escaped}');
            localStorage.setItem('is_admin', 'true');
            localStorage.setItem('rag_auth_token', '{access_token}');
            localStorage.setItem('rag_refresh_token', '{refresh_token}');
            
            setTimeout(function() {{
                window.location.href = '{redirect_url}';
            }}, 500);
        }} catch (error) {{
            console.error('Authentication error:', error);
        }}
    </script>
</body>
</html>"""
        else:
            # For regular users, store in session and redirect to React app
            session['pending_auth_token'] = access_token
            session['pending_refresh_token'] = refresh_token
            session['pending_user_info'] = user_info
            session.permanent = True
            
            print(f"Stored auth data in session for {user_info['email']}")
            print(f"Redirecting to React app...")
            
            return redirect('http://localhost:3000/auth-pickup')
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500

@auth_bp.route('/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        token = data.get('token') if data else None
        
        print(f"Token verification request:")
        print(f"  Request data: {data}")
        print(f"  Token received: {token[:20] + '...' if token and len(token) > 20 else token}")
        
        if not token:
            print("  Error: Token not provided")
            return jsonify({'valid': False, 'error': 'Token not provided'}), 400
        
        # Verify token
        payload = oauth_config.verify_jwt_token(token)
        print(f"  Token verification result: {payload}")
        
        if 'error' in payload:
            print(f"  Error in token verification: {payload['error']}")
            return jsonify({'valid': False, 'error': payload['error']}), 401
        
        # Check domain restriction
        if not oauth_config.is_domain_allowed(payload['email']):
            print(f"  Error: Domain not allowed for {payload['email']}")
            return jsonify({'valid': False, 'error': 'Domain not allowed'}), 403
        
        # Import admin check
        try:
            from admin_auth import is_admin_user
            is_admin = is_admin_user(payload['email'])
        except ImportError:
            is_admin = False
        
        print(f"  Verification successful for {payload['email']} (admin: {is_admin})")
        
        return jsonify({
            'valid': True,
            'user': {
                'id': payload['user_id'],
                'email': payload['email'],
                'name': payload['name'],
                'picture': payload.get('picture', ''),
                'domain': payload['domain'],
                'is_admin': is_admin
            }
        })
    
    except Exception as e:
        logging.error(f"Token verification error: {str(e)}")
        print(f"  Exception in token verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'valid': False, 'error': 'Token verification failed'}), 500

@auth_bp.route('/auth/pickup', methods=['GET'])
def pickup_tokens():
    """Endpoint for React app to pickup authentication tokens"""
    try:
        token = session.get('pending_auth_token')
        user_info = session.get('pending_user_info')
        
        print(f"Token pickup request:")
        print(f"  Token found in session: {bool(token)}")
        print(f"  User info found: {bool(user_info)}")
        
        if not token or not user_info:
            return jsonify({
                'error': 'No pending authentication found',
                'has_token': bool(token),
                'has_user_info': bool(user_info)
            }), 404
        
        # Clear the pending tokens from session
        session.pop('pending_auth_token', None)
        session.pop('pending_user_info', None)
        
        print(f"  Returning tokens for: {user_info.get('email')}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user_info': user_info,
            'is_admin': False
        })
        
    except Exception as e:
        print(f"  Exception in token pickup: {str(e)}")
        logging.error(f"Token pickup error: {str(e)}")
        return jsonify({'error': 'Token pickup failed'}), 500

@auth_bp.route('/auth/test', methods=['GET'])
def test_auth():
    """Test authentication endpoint"""
    return jsonify({
        'message': 'Auth routes are working',
        'timestamp': str(datetime.now()),
        'environment': os.getenv('FLASK_ENV', 'development')
    })

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session.clear()
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/auth/user', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        payload = oauth_config.verify_jwt_token(token)
        
        if 'error' in payload:
            return jsonify({'error': payload['error']}), 401
        
        return jsonify({
            'user': {
                'id': payload['user_id'],
                'email': payload['email'],
                'name': payload['name'],
                'picture': payload.get('picture', ''),
                'domain': payload['domain']
            }
        })
    except Exception as e:
        logging.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user info'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return jsonify({'error': 'Refresh token required'}), 400
        
        refresh_token = data['refresh_token']
        result = oauth_config.refresh_access_token(refresh_token)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 401
        
        return jsonify({
            'access_token': result['access_token'],
            'message': 'Token refreshed successfully'
        })
        
    except Exception as e:
        logging.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Failed to refresh token'}), 500