# WSGI Configuration for Plesk Deployment
import sys
import os

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from chat_api import create_app

# Create the WSGI application
application = create_app()

if __name__ == "__main__":
    application.run()