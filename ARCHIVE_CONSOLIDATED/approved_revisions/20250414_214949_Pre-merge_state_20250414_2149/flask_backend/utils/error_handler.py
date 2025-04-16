import logging
import traceback
from flask import jsonify, current_app

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors with status code"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert exception to a dictionary for JSON response"""
        result = dict(self.payload or {})
        result['error'] = self.message
        result['status_code'] = self.status_code
        return result

# GoCardless-specific exception classes
class GoCardlessError(Exception):
    """Base exception for GoCardless API errors"""
    
    def __init__(self, message, error_type=None, error_code=None, http_status=400, details=None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
    
    def to_dict(self):
        """Convert exception to a dictionary for JSON response"""
        result = {
            'error': self.message,
            'error_type': self.error_type,
            'status_code': self.http_status
        }
        
        if self.error_code:
            result['error_code'] = self.error_code
        
        if self.details:
            result['details'] = self.details
            
        return result

class GoCardlessAuthError(GoCardlessError):
    """Exception for GoCardless OAuth authentication errors"""
    
    def __init__(self, message, error_type="oauth_error", error_code=None, http_status=401, details=None):
        super().__init__(message, error_type, error_code, http_status, details)

class GoCardlessBankConnectionError(GoCardlessError):
    """Exception for errors when connecting to banks through GoCardless"""
    
    def __init__(self, message, error_type="bank_connection_error", error_code=None, http_status=400, details=None):
        super().__init__(message, error_type, error_code, http_status, details)

class GoCardlessTransactionError(GoCardlessError):
    """Exception for errors when working with transactions through GoCardless"""
    
    def __init__(self, message, error_type="transaction_error", error_code=None, http_status=400, details=None):
        super().__init__(message, error_type, error_code, http_status, details)

class GoCardlessWebhookError(GoCardlessError):
    """Exception for errors when processing GoCardless webhooks"""
    
    def __init__(self, message, error_type="webhook_error", error_code=None, http_status=400, details=None):
        super().__init__(message, error_type, error_code, http_status, details)

def handle_error(error):
    """
    Global error handler for all exceptions
    
    Args:
        error: The exception object
        
    Returns:
        JSON response with error details
    """
    # Get detailed error info for logging
    error_class = error.__class__.__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    # Log the error
    logger.error(f"{error_class}: {error_message}\n{error_traceback}")
    
    # Handle custom API errors
    if isinstance(error, APIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    # Handle other exceptions
    status_code = 500
    error_data = {
        'error': 'Internal Server Error',
        'message': error_message if current_app.debug else 'An unexpected error occurred',
        'status_code': status_code
    }
    
    # Include stack trace in debug mode
    if current_app.debug:
        error_data['traceback'] = error_traceback
    
    response = jsonify(error_data)
    response.status_code = status_code
    return response

def handle_gocardless_error(error):
    """
    Error handler for GoCardless-specific exceptions
    
    Args:
        error: The GoCardlessError exception object
        
    Returns:
        JSON response with detailed error information
    """
    # Get detailed error info for logging
    error_class = error.__class__.__name__
    error_message = str(error.message)
    error_traceback = traceback.format_exc()
    
    # Log the error
    logger.error(f"GoCardless Error - {error_class}: {error_message}\n{error_traceback}")
    
    # Create response
    response = jsonify(error.to_dict())
    response.status_code = error.http_status
    
    return response
