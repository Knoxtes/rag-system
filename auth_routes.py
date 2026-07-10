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
        
        # Use 'consent' prompt to ensure we always get a refresh token
        # This is critical for maintaining long-term access
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Changed from 'select_account' to ensure refresh token
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
        
        # Validate CSRF state parameter
        state = request.args.get('state')
        session_state = session.get('oauth_state')

        if not state or state != session_state:
            if os.getenv('FLASK_ENV') != 'production':
                logging.warning(f"OAuth state mismatch (dev mode): received={state}, session={session_state}")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Exchange code for tokens
        flow = oauth_config.get_flow()
        flow.redirect_uri = oauth_config.redirect_uri
        
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
        except Exception as e:
            logging.error(f"Token exchange error: {str(e)}")
            return jsonify({'error': 'Failed to exchange authorization code', 'details': str(e)}), 400
        
        # Get user info
        try:
            user_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_service.userinfo().get().execute()

            # Only store Drive credentials for the admin user (used by indexer)
            from admin_auth import is_admin_user
            if is_admin_user(user_info['email']):
                import pickle
                from config import TOKEN_FILE
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(credentials, token)
                print(f"Saved Google Drive credentials for admin {user_info['email']}")

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
            import html as html_mod
            safe_name = html_mod.escape(user_info.get('name', user_info['email']))

            auth_data = json.dumps({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_info': user_info,
                'redirect': '/admin/dashboard?auth_complete=true',
            })

            return f"""<!DOCTYPE html>
<html>
<head>
    <title>Admin Authentication Success</title>
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
        <h2 class="success">Authentication Successful!</h2>
        <p class="admin">Welcome to the Admin Dashboard, {safe_name}!</p>
        <p class="progress" id="progress">Preparing authentication data...</p>
    </div>

    <script id="auth-data" type="application/json">{auth_data}</script>
    <script>
        try {{
            var d = JSON.parse(document.getElementById('auth-data').textContent);
            localStorage.setItem('authToken', d.access_token);
            localStorage.setItem('user_info', JSON.stringify(d.user_info));
            localStorage.setItem('is_admin', 'true');
            localStorage.setItem('rag_auth_token', d.access_token);
            localStorage.setItem('rag_refresh_token', d.refresh_token);
            setTimeout(function() {{ window.location.href = d.redirect; }}, 500);
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
            
            return redirect('/auth-pickup')
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
        
        if not token:
            return jsonify({'valid': False, 'error': 'Token not provided'}), 400

        payload = oauth_config.verify_jwt_token(token)

        if 'error' in payload:
            logging.debug(f"Token verification failed: {payload['error']}")
            return jsonify({'valid': False, 'error': payload['error']}), 401

        if not oauth_config.is_domain_allowed(payload['email']):
            return jsonify({'valid': False, 'error': 'Domain not allowed'}), 403

        try:
            from admin_auth import is_admin_user
            is_admin = is_admin_user(payload['email'])
        except ImportError:
            is_admin = False
        
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
        logging.error(f"Token verification error: {str(e)}")
        return jsonify({'valid': False, 'error': 'Token verification failed'}), 500

@auth_bp.route('/auth/pickup', methods=['GET'])
def pickup_tokens():
    """Endpoint for React app to pickup authentication tokens"""
    try:
        token = session.get('pending_auth_token')
        refresh_token = session.get('pending_refresh_token')
        user_info = session.get('pending_user_info')
        
        if not token or not user_info:
            return jsonify({
                'error': 'No pending authentication found',
                'has_token': bool(token),
                'has_user_info': bool(user_info)
            }), 404
        
        # Clear the pending tokens from session
        session.pop('pending_auth_token', None)
        session.pop('pending_refresh_token', None)
        session.pop('pending_user_info', None)
        
        return jsonify({
            'success': True,
            'token': token,
            'refresh_token': refresh_token,  # Include refresh token
            'user_info': user_info,
            'is_admin': False
        })
        
    except Exception as e:
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