# WSGI Configuration for Production Deployment (Plesk/Passenger)
import sys
import os
import logging

# Add the application directory to Python path
application_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, application_path)

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler(os.path.join(application_path, 'logs', 'wsgi.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Initializing WSGI application...")

try:
    # Import the Flask app
    from chat_api import create_app
    
    # Create the WSGI application
    application = create_app()
    logger.info("WSGI application initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize WSGI application: {e}", exc_info=True)
    raise

if __name__ == "__main__":
    application.run()