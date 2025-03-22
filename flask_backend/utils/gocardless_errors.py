"""
GoCardless Error Handling Module
Provides specific exception types and error parsing for GoCardless API errors
"""
import json
import logging
from flask_backend.utils.error_handler import APIError

logger = logging.getLogger(__name__)

class GoCardlessError(Exception):
    """Base exception for GoCardless API errors"""
    
    def __init__(self, message, error_type=None, error_code=None, error_response=None, http_status=None, details=None):
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.error_response = error_response
        self.http_status = http_status
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to a dictionary for API responses"""
        return {
            'error': True,
            'message': self.message,
            'error_type': self.error_type,
            'error_code': self.error_code,
            'http_status': self.http_status,
            'details': self.details
        }

class GoCardlessAuthError(GoCardlessError):
    """Raised for authentication and authorization errors"""
    pass

class GoCardlessBankConnectionError(GoCardlessError):
    """Raised for errors related to bank connections"""
    pass

class GoCardlessWebhookError(GoCardlessError):
    """Raised for errors related to webhook processing"""
    pass

class GoCardlessTransactionError(GoCardlessError):
    """Raised for errors related to transaction fetching and processing"""
    pass

def parse_error_response(response, error_prefix="GoCardless API Error"):
    """
    Parse an error response from the GoCardless API
    
    Args:
        response: The requests.Response object
        error_prefix: Prefix for the error message
        
    Returns:
        A GoCardlessError or subclass instance
    """
    try:
        # Try to parse JSON response
        error_data = response.json()
        
        # Different APIs might format errors differently
        if 'error' in error_data:
            # OAuth errors
            error_type = error_data.get('error')
            error_description = error_data.get('error_description', 'No description provided')
            
            message = f"{error_prefix}: {error_description}"
            
            # Create specific error type based on OAuth error
            if error_type in ['invalid_grant', 'invalid_token']:
                return GoCardlessAuthError(
                    message=message,
                    error_type=error_type,
                    error_response=error_data,
                    http_status=response.status_code
                )
        
        elif 'error_code' in error_data:
            # API errors
            error_code = error_data.get('error_code')
            error_description = error_data.get('error_description', 'No description provided')
            
            message = f"{error_prefix}: {error_description}"
            
            # Determine error type based on error code
            if error_code in ['unauthorized', 'forbidden', 'invalid_token']:
                return GoCardlessAuthError(
                    message=message,
                    error_code=error_code,
                    error_response=error_data,
                    http_status=response.status_code
                )
            elif error_code in ['bank_account_not_found', 'institution_not_found', 'connection_failed']:
                return GoCardlessBankConnectionError(
                    message=message,
                    error_code=error_code,
                    error_response=error_data,
                    http_status=response.status_code
                )
            elif error_code in ['transactions_not_found', 'transaction_fetch_failed']:
                return GoCardlessTransactionError(
                    message=message,
                    error_code=error_code,
                    error_response=error_data,
                    http_status=response.status_code
                )
        
        # Default case - use generic details from response
        return GoCardlessError(
            message=f"{error_prefix}: {response.text}",
            http_status=response.status_code,
            error_response=error_data
        )
        
    except (json.JSONDecodeError, ValueError):
        # Failed to parse JSON, use text response
        return GoCardlessError(
            message=f"{error_prefix}: {response.text if response.text else 'Unknown error'}",
            http_status=response.status_code
        )

def handle_gocardless_error(error):
    """
    Convert a GoCardlessError to an APIError for consistent API responses
    
    Args:
        error: A GoCardlessError instance
        
    Returns:
        An APIError instance
    """
    status_code = error.http_status if error.http_status else 400
    
    logger.error(f"GoCardless error: {error.message}")
    
    if isinstance(error, GoCardlessAuthError):
        # Auth errors should return 401
        status_code = 401
    elif isinstance(error, GoCardlessBankConnectionError):
        # Connection errors vary
        status_code = status_code if status_code != 400 else 400
    elif isinstance(error, GoCardlessWebhookError):
        # Webhook errors typically 400
        status_code = status_code if status_code != 400 else 400
    
    return APIError(
        message=error.message,
        status_code=status_code,
        payload=error.to_dict()
    )