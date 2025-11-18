"""
Production WSGI application for deployment on Plesk/cPanel
"""

import os
import sys
import logging
from pathlib import Path

# Add project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.production
from dotenv import load_dotenv
load_dotenv('.env.production')

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler()
    ]
)

# Import Flask app
try:
    from chat_api import app as application
    
    # Production-specific configurations
    application.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
    )
    
    # Add security headers
    @application.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    logging.info("RAG System production WSGI application started successfully")
    
except Exception as e:
    logging.error(f"Failed to start RAG System: {e}")
    raise

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)