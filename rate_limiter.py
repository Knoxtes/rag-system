# rate_limiter.py - Shared rate limiter instance
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create the limiter instance that will be shared across the app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
