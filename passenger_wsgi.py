#!/usr/bin/env python3
"""
WSGI Configuration for Plesk/Passenger Deployment

This is the entry point for the WSGI server (Passenger).
Handles proper initialization, logging, and error recovery.
"""

import sys
import os
import logging

# ============================================
# Path Configuration
# ============================================
# Get absolute path to application directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Change working directory to app directory
os.chdir(APP_DIR)

# ============================================
# Environment Setup
# ============================================
# Load environment variables from .env.production
from dotenv import load_dotenv
env_file = os.path.join(APP_DIR, '.env.production')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to regular .env
    load_dotenv()

# ============================================
# Logging Configuration
# ============================================
log_dir = os.path.join(APP_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'passenger.log')),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('passenger_wsgi')

# ============================================
# Suppress Noisy Libraries
# ============================================
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.cloud').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)

# ============================================
# Application Factory
# ============================================
try:
    logger.info("Initializing RAG Chat Application...")
    
    # Import and create the Flask application
    from chat_api import create_app
    application = create_app()
    
    # Production security headers
    @application.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    logger.info("RAG Chat Application initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    import traceback
    logger.error(traceback.format_exc())
    
    # Create a minimal error application
    from flask import Flask, jsonify
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return jsonify({
            'status': 'error',
            'message': 'Application failed to initialize. Check server logs for details.',
        }), 500

    @application.route('/health')
    def health_check():
        return jsonify({
            'status': 'unhealthy',
            'message': 'Application failed to initialize.',
        }), 503

# ============================================
# Development Server (when run directly)
# ============================================
if __name__ == "__main__":
    logger.info("Starting development server...")
    application.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )