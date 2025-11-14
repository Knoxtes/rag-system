"""
Google OAuth Configuration for RAG System
Handles authentication and organization domain restrictions
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
import google.auth.transport.requests
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import jwt

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class OAuthConfig:
    def __init__(self):
        # OAuth Configuration
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        # Organization Configuration
        self.allowed_domains = os.getenv('ALLOWED_DOMAINS', '').split(',')
        self.allowed_domains = [domain.strip() for domain in self.allowed_domains if domain.strip()]
        
        # Security Configuration
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.token_expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
        
        # OAuth Scopes - Include Google Drive scopes
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate OAuth configuration"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
        
        if not self.allowed_domains:
            print("WARNING: No allowed domains specified. All authenticated users will be allowed.")
    
    def get_flow(self):
        """Create OAuth flow"""
        # Load actual client configuration from credentials.json
        import json
        try:
            with open('credentials.json', 'r') as f:
                client_config = json.load(f)
            
            # Handle both web and installed app configurations
            if 'web' in client_config:
                config = client_config
            elif 'installed' in client_config:
                # Convert installed app config to web config format
                config = {
                    "web": {
                        "client_id": client_config['installed']['client_id'],
                        "client_secret": client_config['installed']['client_secret'],
                        "auth_uri": client_config['installed']['auth_uri'],
                        "token_uri": client_config['installed']['token_uri'],
                        "redirect_uris": [self.redirect_uri]
                    }
                }
            else:
                raise ValueError("Invalid credentials.json format")
            
            return Flow.from_client_config(config, scopes=self.scopes)
        except FileNotFoundError:
            # Fallback to environment variables if credentials.json not found
            return Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
    
    def generate_jwt_token(self, user_info):
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': user_info['id'],
            'email': user_info['email'],
            'name': user_info['name'],
            'picture': user_info.get('picture', ''),
            'domain': user_info['email'].split('@')[1] if '@' in user_info['email'] else '',
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def is_domain_allowed(self, email):
        """Check if user's domain is in allowed list"""
        if not self.allowed_domains:
            return True  # Allow all if no restrictions set
        
        domain = email.split('@')[1] if '@' in email else ''
        return domain in self.allowed_domains

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Get OAuth config
        oauth_config = OAuthConfig()
        
        # Verify token
        payload = oauth_config.verify_jwt_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error'], 'code': 'INVALID_TOKEN'}), 401
        
        # Check domain restriction
        if not oauth_config.is_domain_allowed(payload['email']):
            return jsonify({'error': 'Domain not allowed', 'code': 'DOMAIN_NOT_ALLOWED'}), 403
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

# Global OAuth instance
oauth_config = OAuthConfig()