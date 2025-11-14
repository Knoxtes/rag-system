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
        # Get authorization code (this is the most important part)
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        # Get state parameter
        state = request.args.get('state')
        session_state = session.get('oauth_state')
        
        # In development, be more lenient with state validation
        if os.getenv('FLASK_ENV') == 'production':
            # Strict validation in production
            if not state or state != session_state:
                return jsonify({'error': 'Invalid state parameter'}), 400
        else:
            # Development mode: just log for debugging but allow through
            print(f"Development OAuth callback:")
            print(f"  Received state: {state}")
            print(f"  Session state: {session_state}")
            print(f"  Code received: {code[:20]}..." if code else "  No code")
        
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
        
        # Generate JWT token
        jwt_token = oauth_config.generate_jwt_token(user_info)
        
        # Store token in session temporarily for pickup by dashboard
        session['pending_auth_token'] = jwt_token
        session['pending_user_info'] = user_info
        session.permanent = True
        
        # Create a simple redirect page that will handle the token transfer
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Success</title>
            <script>
                // Store the token immediately
                localStorage.setItem('authToken', '{jwt_token}');
                localStorage.setItem('user_info', '{json.dumps(user_info).replace("'", "\\'")}');
                
                // Redirect immediately
                window.location.href = '/admin/dashboard?auth_complete=true';
            </script>
        </head>
        <body>
            <p>Authentication successful! Redirecting...</p>
            <script>
                // Fallback if the above doesn't work
                setTimeout(function() {{
                    window.location.href = '/admin/dashboard?auth_complete=true';
                }}, 1000);
            </script>
        </body>
        </html>
        """
        
        # Prepare user info for JavaScript (escape quotes properly)
        user_info_json = json.dumps(user_info).replace('"', '\\"')
        
        # Return success response with token
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: #f0f2f5; }}
                .success {{ color: #4CAF50; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .loading {{ display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite; margin-left: 10px; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">✅ Authentication Successful!</h1>
                <p>Welcome, {user_info['name']}!</p>
                <p>Redirecting you to the application...<span class="loading"></span></p>
                <script>
                    function completeAuth() {{
                        try {{
                            // Store token in localStorage
                            localStorage.setItem('authToken', '{jwt_token}');
                            localStorage.setItem('user_info', "{user_info_json}");
                            
                            console.log('Token stored successfully:', localStorage.getItem('authToken'));
                            
                            // Immediate redirect to admin dashboard with auth parameter
                            window.location.replace('http://localhost:5000/admin/dashboard?auth_complete=true&t=' + Date.now());
                            
                        }} catch (error) {{
                            console.error('Error storing auth data:', error);
                            document.body.innerHTML = '<div class="container"><h1 style="color: red;">Error</h1><p>Failed to store authentication data. Error: ' + error.message + '</p><button onclick="window.location.href=\\'/admin/dashboard\\'">Try Again</button></div>';
                        }}
                    }}
                    
                    // Start immediately
                    completeAuth();
                        document.body.innerHTML = '<div class="container"><h1 style="color: red;">Error</h1><p>Failed to store authentication data. Please try again.</p></div>';
                    }}
                </script>
            </div>
        </body>
        </html>
        """
    
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500
    
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500

@auth_bp.route('/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'valid': False, 'error': 'Token not provided'}), 400
        
        # Verify token
        payload = oauth_config.verify_jwt_token(token)
        
        if 'error' in payload:
            return jsonify({'valid': False, 'error': payload['error']}), 401
        
        # Check domain restriction
        if not oauth_config.is_domain_allowed(payload['email']):
            return jsonify({'valid': False, 'error': 'Domain not allowed'}), 403
        
        # Import admin check
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
        return jsonify({'valid': False, 'error': 'Token verification failed'}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        # Clear session
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