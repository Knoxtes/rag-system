"""
Error handling utilities for production-ready error responses
"""
import logging
from flask import jsonify, current_app
from functools import wraps

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary for JSON response"""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status'] = self.status_code
        return rv


class ValidationError(AppError):
    """Input validation error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class AuthenticationError(AppError):
    """Authentication error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=401, payload=payload)


class AuthorizationError(AppError):
    """Authorization error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=403, payload=payload)


class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=429, payload=payload)


class ServiceUnavailableError(AppError):
    """Service unavailable error"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=503, payload=payload)


def sanitize_error_message(error, debug=False):
    """
    Sanitize error messages for production
    
    Args:
        error: Exception or error message
        debug: Whether to include detailed error info
    
    Returns:
        str: Sanitized error message
    """
    if debug:
        return str(error)
    
    # Map error types to user-friendly messages
    error_str = str(error).lower()
    
    if 'connection' in error_str or 'timeout' in error_str:
        return 'Service temporarily unavailable. Please try again.'
    elif 'authentication' in error_str or 'unauthorized' in error_str:
        return 'Authentication failed. Please log in again.'
    elif 'not found' in error_str:
        return 'The requested resource was not found.'
    elif 'permission' in error_str or 'forbidden' in error_str:
        return 'You do not have permission to access this resource.'
    elif 'rate limit' in error_str:
        return 'Too many requests. Please try again later.'
    else:
        return 'An unexpected error occurred. Please try again.'


def handle_errors(f):
    """
    Decorator to handle errors in Flask routes
    
    Usage:
        @app.route('/endpoint')
        @handle_errors
        def my_endpoint():
            # Your code here
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            logger.warning(f"Application error in {f.__name__}: {e.message}")
            return jsonify(e.to_dict()), e.status_code
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'error': sanitize_error_message(e, current_app.debug),
                'status': 400
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'error': sanitize_error_message(e, current_app.debug),
                'status': 500
            }), 500
    
    return decorated_function


def validate_required_fields(data, required_fields):
    """
    Validate that required fields are present in request data
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
    
    Raises:
        ValidationError: If any required field is missing
    """
    if not data:
        raise ValidationError('Request body is required')
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            payload={'missing_fields': missing_fields}
        )


def validate_string_length(value, field_name, min_length=None, max_length=None):
    """
    Validate string length
    
    Args:
        value: String value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    if min_length and len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if max_length and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")


def validate_enum(value, field_name, allowed_values):
    """
    Validate that a value is in an allowed set
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        allowed_values: List of allowed values
    
    Raises:
        ValidationError: If value is not in allowed set
    """
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(map(str, allowed_values))}",
            payload={'allowed_values': allowed_values}
        )


def validate_file_id(file_id):
    """
    Validate Google Drive file ID format
    
    Args:
        file_id: File ID to validate
    
    Raises:
        ValidationError: If file ID is invalid
    """
    if not file_id:
        raise ValidationError('File ID is required')
    
    if not isinstance(file_id, str):
        raise ValidationError('File ID must be a string')
    
    if len(file_id) > 200:
        raise ValidationError('File ID is too long')
    
    # Basic format check (alphanumeric, hyphens, underscores)
    if not all(c.isalnum() or c in '-_' for c in file_id):
        raise ValidationError('File ID contains invalid characters')


def register_error_handlers(app):
    """
    Register error handlers for Flask app
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found', 'status': 404}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed', 'status': 405}), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        message = str(error) if app.debug else 'Internal server error'
        return jsonify({'error': message, 'status': 500}), 500
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(error.to_dict()), error.status_code
