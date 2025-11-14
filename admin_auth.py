"""
Admin Authentication and Authorization
Restrictive admin access for specific Google account
"""

from functools import wraps
from flask import request, jsonify
from oauth_config import oauth_config

# Specific admin email - only this account has admin access
ADMIN_EMAIL = 'esexton@7mountainsmedia.com'

def require_admin(f):
    """Decorator to require admin authentication - only specific email allowed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        payload = oauth_config.verify_jwt_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error'], 'code': 'INVALID_TOKEN'}), 401
        
        # Check if user is the specific admin
        if payload.get('email') != ADMIN_EMAIL:
            return jsonify({
                'error': 'Admin access denied', 
                'code': 'ADMIN_ACCESS_DENIED',
                'message': 'This page is restricted to system administrators only.'
            }), 403
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

def is_admin_user(email):
    """Check if email is the admin user"""
    return email == ADMIN_EMAIL
