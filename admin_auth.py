"""
Admin Authentication and Authorization
Restrictive admin access for specific Google account(s)
"""

import os
from functools import wraps
from flask import request, jsonify
from oauth_config import oauth_config

_FALLBACK_ADMIN = 'esexton@7mountainsmedia.com'

def _get_admin_emails():
    env_val = os.getenv('ADMIN_EMAILS', '').strip()
    if env_val:
        return {e.strip().lower() for e in env_val.split(',') if e.strip()}
    return {_FALLBACK_ADMIN}

ADMIN_EMAILS = _get_admin_emails()

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401

        token = auth_header.split(' ')[1]

        payload = oauth_config.verify_jwt_token(token)
        if 'error' in payload:
            return jsonify({'error': payload['error'], 'code': 'INVALID_TOKEN'}), 401

        if payload.get('email', '').lower() not in ADMIN_EMAILS:
            return jsonify({
                'error': 'Admin access denied',
                'code': 'ADMIN_ACCESS_DENIED',
                'message': 'This page is restricted to system administrators only.'
            }), 403

        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function

def is_admin_user(email):
    """Check if email is an admin user"""
    return email.lower() in ADMIN_EMAILS
