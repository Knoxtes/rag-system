"""
Alternative WSGI entry point for production deployment.
For Plesk deployment, use passenger_wsgi.py instead.
"""

import sys
import os

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app with production configuration
from chat_api import create_app

# Create the WSGI application
application = create_app()

if __name__ == "__main__":
    # For local testing in production mode
    application.run(host='0.0.0.0', port=5000, debug=False)