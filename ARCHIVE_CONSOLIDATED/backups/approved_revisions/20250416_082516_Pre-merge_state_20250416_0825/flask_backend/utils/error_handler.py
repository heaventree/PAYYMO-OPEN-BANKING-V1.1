"""
Error Handler Utility

This module provides error handling utilities for the Flask application,
including custom exceptions and error handlers for various HTTP error codes.
It centralizes error handling to ensure consistent responses across the application.
"""
import logging
import traceback
import json
from datetime import datetime
from flask import jsonify, current_app, request, g

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
    # Enhanced error logging
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': error.__class__.__name__,
        'message': str(error),
        'path': request.path if request else None,
        'method': request.method if request else None,
        'ip': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request and request.user_agent else None
    }
    
    # Handle API errors
    if isinstance(error, APIError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        
        # For security errors, ensure we don't expose sensitive information
        if hasattr(error, 'is_security_error') and error.is_security_error:
            logger.warning(f"Security error: {json.dumps(log_data)}")
        else:
            logger.error(f"API error: {json.dumps(log_data)}")
            
        return response
    
    # Log other errors with full traceback
    log_data['traceback'] = traceback.format_exc()
    logger.error(f"Unexpected error: {json.dumps(log_data)}")
    
    # Return 500 error for unexpected exceptions
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'message': str(error) if current_app.config.get('DEBUG', False) else 'An unexpected error occurred',
        'request_id': request.headers.get('X-Request-ID') if request else None
    }), 500

class APIError(Exception):
    """Custom exception for API errors with status code"""
    
    def __init__(self, message, status_code=400, payload=None, is_security_error=False):
        """
        Initialize API error
        
        Args:
            message: Error message
            status_code: HTTP status code
            payload: Additional error data
            is_security_error: Whether this is a security-related error
        """
        self.message = message
        self.status_code = status_code
        self.payload = payload
        self.is_security_error = is_security_error
        self.error_id = f"err_{int(datetime.utcnow().timestamp())}"
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
        error_dict['error_id'] = self.error_id
        
        # Add timestamp for all errors
        error_dict['timestamp'] = datetime.utcnow().isoformat()
        
        # Add request ID if available
        if request and request.headers.get('X-Request-ID'):
            error_dict['request_id'] = request.headers.get('X-Request-ID')
            
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
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'BadRequest',
            'message': str(error),
            'path': request.path if request else None,
            'method': request.method if request else None
        }
        logger.warning(f"Bad request error: {json.dumps(log_data)}")
        
        return jsonify({
            'status': 'error',
            'error': 'Bad request',
            'message': str(error),
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 400, {'Cache-Control': 'no-store'}
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors"""
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'Unauthorized',
            'message': str(error),
            'path': request.path if request else None,
            'method': request.method if request else None
        }
        logger.warning(f"Unauthorized error: {json.dumps(log_data)}")
        
        return jsonify({
            'status': 'error',
            'error': 'Unauthorized',
            'message': 'Authentication required',  # Generic message for security
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 401, {'Cache-Control': 'no-store', 'WWW-Authenticate': 'Bearer'}
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors"""
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'Forbidden',
            'message': str(error),
            'path': request.path if request else None,
            'method': request.method if request else None,
            'user_id': getattr(g, 'current_user', {}).get('sub') if hasattr(g, 'current_user') else None
        }
        logger.warning(f"Forbidden error: {json.dumps(log_data)}")
        
        return jsonify({
            'status': 'error',
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',  # Generic message for security
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 403, {'Cache-Control': 'no-store'}
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'NotFound',
            'path': request.path if request else None,
            'method': request.method if request else None
        }
        # Only log as info since 404s are common and not critical
        logger.info(f"Not found error: {json.dumps(log_data)}")
        
        return jsonify({
            'status': 'error',
            'error': 'Not found',
            'message': 'The requested resource could not be found',
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 404, {'Cache-Control': 'no-store'}
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded errors"""
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'RateLimitExceeded',
            'path': request.path if request else None,
            'method': request.method if request else None,
            'ip': request.remote_addr if request else None
        }
        logger.warning(f"Rate limit exceeded: {json.dumps(log_data)}")
        
        # Calculate retry after time (usually 1 minute for most rate limits)
        retry_after = 60
        
        return jsonify({
            'status': 'error',
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 429, {'Cache-Control': 'no-store', 'Retry-After': str(retry_after)}
    
    @app.errorhandler(500)
    def handle_server_error(error):
        """Handle internal server errors"""
        error_id = f"err_{int(datetime.utcnow().timestamp())}"
        log_data = {
            'error_id': error_id,
            'error_type': 'InternalServerError',
            'message': str(error),
            'path': request.path if request else None,
            'method': request.method if request else None,
            'traceback': traceback.format_exc()
        }
        logger.error(f"Internal server error: {json.dumps(log_data)}")
        
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request.headers.get('X-Request-ID') if request else None
        }), 500, {'Cache-Control': 'no-store'}
    
    logger.info("Error handlers registered successfully")