"""
Input Validation Utilities for Production Security
Provides sanitization and validation functions for user inputs
"""

import re
from typing import Any, Optional
from flask import jsonify


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """Validates and sanitizes user inputs"""
    
    # Maximum lengths for various inputs
    MAX_MESSAGE_LENGTH = 10000  # 10K characters for chat messages
    MAX_COLLECTION_NAME_LENGTH = 100
    MAX_FILE_ID_LENGTH = 200
    MAX_QUERY_LENGTH = 500  # For search queries
    
    # Pattern for valid Google Drive file IDs (alphanumeric, hyphens, underscores)
    FILE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{10,200}$')
    
    # Pattern for valid collection names (alphanumeric, underscores, hyphens)
    COLLECTION_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
    
    @staticmethod
    def validate_message(message: Any) -> str:
        """
        Validate and sanitize chat message
        
        Args:
            message: User input message
            
        Returns:
            Validated message string
            
        Raises:
            ValidationError: If message is invalid
        """
        if not message:
            raise ValidationError("Message cannot be empty")
        
        if not isinstance(message, str):
            raise ValidationError("Message must be a string")
        
        # Strip whitespace
        message = message.strip()
        
        if not message:
            raise ValidationError("Message cannot be empty or whitespace only")
        
        if len(message) > InputValidator.MAX_MESSAGE_LENGTH:
            raise ValidationError(f"Message too long (max {InputValidator.MAX_MESSAGE_LENGTH} characters)")
        
        # Remove any null bytes
        message = message.replace('\x00', '')
        
        return message
    
    @staticmethod
    def validate_file_id(file_id: Any) -> Optional[str]:
        """
        Validate Google Drive file ID
        
        Args:
            file_id: File ID to validate
            
        Returns:
            Validated file ID or None if not provided
            
        Raises:
            ValidationError: If file ID is invalid
        """
        if not file_id:
            return None
        
        if not isinstance(file_id, str):
            raise ValidationError("File ID must be a string")
        
        file_id = file_id.strip()
        
        if not InputValidator.FILE_ID_PATTERN.match(file_id):
            raise ValidationError("Invalid file ID format")
        
        return file_id
    
    @staticmethod
    def validate_collection_name(collection: Any) -> Optional[str]:
        """
        Validate collection name
        
        Args:
            collection: Collection name to validate
            
        Returns:
            Validated collection name or None if not provided
            
        Raises:
            ValidationError: If collection name is invalid
        """
        if not collection:
            return None
        
        if not isinstance(collection, str):
            raise ValidationError("Collection name must be a string")
        
        collection = collection.strip()
        
        # Allow special "ALL_COLLECTIONS" value
        if collection == "ALL_COLLECTIONS":
            return collection
        
        if not InputValidator.COLLECTION_NAME_PATTERN.match(collection):
            raise ValidationError("Invalid collection name format")
        
        return collection
    
    @staticmethod
    def validate_search_query(query: Any) -> str:
        """
        Validate search query
        
        Args:
            query: Search query to validate
            
        Returns:
            Validated query string
            
        Raises:
            ValidationError: If query is invalid
        """
        if not query:
            raise ValidationError("Search query cannot be empty")
        
        if not isinstance(query, str):
            raise ValidationError("Search query must be a string")
        
        query = query.strip()
        
        if len(query) < 2:
            raise ValidationError("Search query too short (minimum 2 characters)")
        
        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            raise ValidationError(f"Search query too long (max {InputValidator.MAX_QUERY_LENGTH} characters)")
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        return query
    
    @staticmethod
    def validate_pagination(page: Any, per_page: Any) -> tuple:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            Tuple of (page, per_page) as integers
            
        Raises:
            ValidationError: If parameters are invalid
        """
        try:
            page = int(page) if page is not None else 1
            per_page = int(per_page) if per_page is not None else 50
        except (ValueError, TypeError):
            raise ValidationError("Invalid pagination parameters")
        
        if page < 1:
            raise ValidationError("Page number must be at least 1")
        
        if per_page < 1:
            raise ValidationError("Per page value must be at least 1")
        
        if per_page > 100:
            raise ValidationError("Per page value cannot exceed 100")
        
        return page, per_page
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe use
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
        
        # Remove path traversal attempts
        filename = filename.replace('../', '').replace('..\\', '')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Replace potentially dangerous characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @staticmethod
    def validate_folder_id(folder_id: Any) -> Optional[str]:
        """
        Validate Google Drive folder ID
        
        Args:
            folder_id: Folder ID to validate
            
        Returns:
            Validated folder ID or None if not provided
            
        Raises:
            ValidationError: If folder ID is invalid
        """
        if not folder_id:
            return None
        
        if not isinstance(folder_id, str):
            raise ValidationError("Folder ID must be a string")
        
        folder_id = folder_id.strip()
        
        # Allow empty string for root folder
        if folder_id == '':
            return folder_id
        
        # Check pattern for Drive IDs
        if not re.match(r'^[a-zA-Z0-9_-]{10,200}$', folder_id):
            raise ValidationError("Invalid folder ID format")
        
        return folder_id


def handle_validation_error(error: ValidationError):
    """
    Handle validation error and return appropriate JSON response
    
    Args:
        error: ValidationError instance
        
    Returns:
        Flask JSON response with error details
    """
    return jsonify({
        'error': 'Validation error',
        'message': str(error),
        'code': 'VALIDATION_ERROR'
    }), 400
