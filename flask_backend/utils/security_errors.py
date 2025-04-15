"""
Security Error Handlers
----------------------
This module provides specialized error handlers for security-related exceptions.
These include authentication failures, authorization failures, input validation
errors, and other security-related issues.

Security errors are handled differently from general errors to provide
secure, consistent responses without leaking sensitive information.
"""

import logging
from flask_backend.utils.error_handler import APIError

# Initialize logging
logger = logging.getLogger(__name__)

class SecurityError(APIError):
    """Base class for all security-related errors"""
    
    def __init__(self, message, status_code=400, payload=None, log_message=None):
        """
        Initialize security error
        
        Args:
            message: Public error message (shown to users)
            status_code: HTTP status code
            payload: Additional error data
            log_message: Private message for logging (not shown to users)
        """
        super().__init__(message, status_code, payload)
        # Log more detailed information that shouldn't be exposed to users
        if log_message:
            logger.warning(f"Security error: {log_message}")
        else:
            logger.warning(f"Security error: {message}")

class AuthenticationError(SecurityError):
    """Error raised when authentication fails"""
    
    def __init__(self, message="Authentication failed", log_message=None, payload=None):
        """Initialize authentication error"""
        super().__init__(message, 401, payload, log_message)

class AuthorizationError(SecurityError):
    """Error raised when a user is not authorized to perform an action"""
    
    def __init__(self, message="You are not authorized to perform this action", log_message=None, payload=None):
        """Initialize authorization error"""
        super().__init__(message, 403, payload, log_message)

class ValidationError(SecurityError):
    """Error raised when input validation fails"""
    
    def __init__(self, message="Invalid input data", errors=None, log_message=None):
        """
        Initialize validation error
        
        Args:
            message: Error message
            errors: Dictionary of field-specific validation errors
            log_message: Private message for logging
        """
        payload = {'errors': errors} if errors else None
        super().__init__(message, 400, payload, log_message)

class RateLimitError(SecurityError):
    """Error raised when rate limit is exceeded"""
    
    def __init__(self, message="Rate limit exceeded. Please try again later.", log_message=None, payload=None):
        """Initialize rate limit error"""
        super().__init__(message, 429, payload, log_message)

class TokenError(SecurityError):
    """Error raised when token validation fails"""
    
    def __init__(self, message="Invalid or expired token", log_message=None, payload=None):
        """Initialize token error"""
        super().__init__(message, 401, payload, log_message)

class CSRFError(SecurityError):
    """Error raised when CSRF validation fails"""
    
    def __init__(self, message="CSRF validation failed", log_message=None, payload=None):
        """Initialize CSRF error"""
        super().__init__(message, 403, payload, log_message)

class InputSanitizationError(SecurityError):
    """Error raised when input sanitization fails"""
    
    def __init__(self, message="Input contains potentially malicious content", log_message=None, payload=None):
        """Initialize input sanitization error"""
        super().__init__(message, 400, payload, log_message)

# Register security error handlers
def register_security_error_handlers(app):
    """
    Register security error handlers with Flask app
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(SecurityError)
    def handle_security_error(error):
        """Handle all security errors"""
        response = error.to_dict()
        # Add security headers to prevent caching of error responses
        headers = {
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        return response, error.status_code, headers
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors"""
        return handle_security_error(error)
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        """Handle authorization errors"""
        return handle_security_error(error)
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        return handle_security_error(error)
    
    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error):
        """Handle rate limit errors"""
        return handle_security_error(error)
    
    @app.errorhandler(TokenError)
    def handle_token_error(error):
        """Handle token errors"""
        return handle_security_error(error)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Handle CSRF errors"""
        return handle_security_error(error)
    
    @app.errorhandler(InputSanitizationError)
    def handle_sanitization_error(error):
        """Handle input sanitization errors"""
        return handle_security_error(error)
        
    logger.info("Security error handlers registered successfully")