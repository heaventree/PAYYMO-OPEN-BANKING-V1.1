import logging
import traceback
from flask import jsonify, current_app

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors with status code"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert exception to a dictionary for JSON response"""
        result = dict(self.payload or {})
        result['error'] = self.message
        result['status_code'] = self.status_code
        return result

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
