"""
Custom exceptions for the RAG system
Provides structured error handling with specific exception types
"""


class RAGSystemException(Exception):
    """Base exception for all RAG system errors"""
    pass


class ConfigurationError(RAGSystemException):
    """Raised when system configuration is invalid or incomplete"""
    pass


class AuthenticationError(RAGSystemException):
    """Raised when Google authentication fails"""
    pass


class VectorStoreError(RAGSystemException):
    """Raised when vector database operations fail"""
    pass


class DocumentProcessingError(RAGSystemException):
    """Raised when document loading or processing fails"""
    pass


class EmbeddingError(RAGSystemException):
    """Raised when embedding generation fails"""
    pass


class QueryError(RAGSystemException):
    """Raised when query processing fails"""
    pass


class APIError(RAGSystemException):
    """Raised when external API calls fail"""
    pass


class OCRError(RAGSystemException):
    """Raised when OCR processing fails"""
    pass


class ValidationError(RAGSystemException):
    """Raised when validation checks fail"""
    pass


# Error codes for structured logging and monitoring
ERROR_CODES = {
    'CONFIG_MISSING': 'E001',
    'CONFIG_INVALID': 'E002',
    'AUTH_FAILED': 'E101',
    'AUTH_TOKEN_EXPIRED': 'E102',
    'VECTOR_DB_CONNECTION': 'E201',
    'VECTOR_DB_QUERY': 'E202',
    'VECTOR_DB_INSERT': 'E203',
    'DOC_DOWNLOAD_FAILED': 'E301',
    'DOC_PARSE_FAILED': 'E302',
    'DOC_UNSUPPORTED_TYPE': 'E303',
    'EMBEDDING_FAILED': 'E401',
    'EMBEDDING_MODEL_LOAD': 'E402',
    'QUERY_INVALID': 'E501',
    'QUERY_TIMEOUT': 'E502',
    'API_RATE_LIMIT': 'E601',
    'API_QUOTA_EXCEEDED': 'E602',
    'API_UNAVAILABLE': 'E603',
    'OCR_FAILED': 'E701',
    'OCR_UNSUPPORTED_FORMAT': 'E702',
    'VALIDATION_FAILED': 'E801',
}


def get_error_code(exception_type: str) -> str:
    """
    Get error code for exception type
    
    Args:
        exception_type: Name of exception or error type
        
    Returns:
        Error code string
    """
    return ERROR_CODES.get(exception_type, 'E999')


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.error_code = ERROR_CODES['API_RATE_LIMIT']


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded"""
    
    def __init__(self, message: str, quota_limit: int = None):
        super().__init__(message)
        self.quota_limit = quota_limit
        self.error_code = ERROR_CODES['API_QUOTA_EXCEEDED']
