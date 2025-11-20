"""
Production WSGI Configuration for Plesk/cPanel Deployment
This is the primary entry point for production deployments.
"""

import sys
import os
import logging

# Suppress harmless gRPC ALTS warnings (appears when running locally, not on GCP)
os.environ.setdefault('GRPC_ENABLE_FORK_SUPPORT', '0')
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.cloud').setLevel(logging.WARNING)

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (tries .env.production, then .env)
from dotenv import load_dotenv
load_dotenv('.env.production')  # Production environment
load_dotenv()  # Fallback to .env if .env.production doesn't exist

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler()
    ]
)

# Import and create the Flask app
try:
    from chat_api import create_app
    
    # Create the WSGI application
    application = create_app()
    
    # Production-specific configurations
    application.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
    )
    
    # Add security headers for production
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
    # For local testing in production mode
    application.run(host='0.0.0.0', port=5000, debug=False)