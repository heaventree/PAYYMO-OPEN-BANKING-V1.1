"""
Error Handler Utility

This module provides error handling utilities for the Flask application.
"""
import logging
import traceback
from flask import jsonify, current_app

# Logger
logger = logging.getLogger(__name__)

def handle_error(error):
    """
    Handle any exception and return a JSON response
    
    Args:
        error: Exception to handle
        
    Returns:
        JSON response with error details
    """
    # Handle API errors
    if isinstance(error, APIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    # Log other errors
    logger.error(f"Unexpected error: {str(error)}")
    logger.error(traceback.format_exc())
    
    # Return 500 error for unexpected exceptions
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'message': str(error) if current_app.config.get('DEBUG', False) else 'An unexpected error occurred'
    }), 500

class APIError(Exception):
    """Custom exception for API errors with status code"""
    
    def __init__(self, message, status_code=400, payload=None):
        """
        Initialize API error
        
        Args:
            message: Error message
            status_code: HTTP status code
            payload: Additional error data
        """
        self.message = message
        self.status_code = status_code
        self.payload = payload
        super().__init__(self.message)
    
    def to_dict(self):
        """
        Convert error to dictionary for JSON response
        
        Returns:
            Dictionary representation of error
        """
        error_dict = dict(self.payload or ())
        error_dict['error'] = self.message
        error_dict['status'] = 'error'
        return error_dict

def register_error_handlers(app):
    """
    Register error handlers with Flask app
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle APIError exceptions"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors"""
        return jsonify({
            'status': 'error',
            'error': 'Bad request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors"""
        return jsonify({
            'status': 'error',
            'error': 'Unauthorized',
            'message': str(error)
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors"""
        return jsonify({
            'status': 'error',
            'error': 'Forbidden',
            'message': str(error)
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        return jsonify({
            'status': 'error',
            'error': 'Not found',
            'message': str(error)
        }), 404
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded errors"""
        return jsonify({
            'status': 'error',
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def handle_server_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    logger.info("Error handlers registered successfully")