import json
import logging
import time
from datetime import datetime
from flask import request
from flask_backend.app import db
from flask_backend.models import ApiLog

logger = logging.getLogger(__name__)

def log_api_request(request_obj):
    """
    Log API request details to database and logger
    
    Args:
        request_obj: The Flask request object
        
    Returns:
        None
    """
    try:
        # Get request start time
        request.start_time = time.time()
        
        # Log request details to logger
        request_data = None
        
        if request_obj.method in ['POST', 'PUT', 'PATCH'] and request_obj.is_json:
            request_data = request_obj.get_json()
            
            # Mask sensitive data
            masked_data = mask_sensitive_data(request_data)
            logger.info(f"API Request: {request_obj.method} {request_obj.path} - {json.dumps(masked_data)}")
        else:
            logger.info(f"API Request: {request_obj.method} {request_obj.path}")
    
    except Exception as e:
        logger.error(f"Error logging API request: {str(e)}")

def log_api_response(response):
    """
    Log API response details to database and logger
    
    Args:
        response: The Flask response object
        
    Returns:
        The original response
    """
    try:
        # Calculate request duration
        duration_ms = int((time.time() - request.start_time) * 1000) if hasattr(request, 'start_time') else 0
        
        # Get request and response data
        endpoint = request.path
        method = request.method
        status_code = response.status_code
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        request_data = None
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            request_data = request.get_json()
        
        response_data = None
        if response.is_json:
            response_data = response.get_json()
        
        # Log to database
        api_log = ApiLog(
            endpoint=endpoint,
            method=method,
            request_data=json.dumps(mask_sensitive_data(request_data)) if request_data else None,
            response_data=json.dumps(response_data) if response_data else None,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            error=response_data.get('error') if response_data and isinstance(response_data, dict) and 'error' in response_data else None
        )
        
        db.session.add(api_log)
        db.session.commit()
        
        # Log to logger
        logger.info(f"API Response: {method} {endpoint} - Status: {status_code}, Duration: {duration_ms}ms")
        
        if status_code >= 400:
            logger.warning(f"API Error: {method} {endpoint} - Status: {status_code}, Error: {response_data.get('error') if response_data and isinstance(response_data, dict) else 'Unknown error'}")
    
    except Exception as e:
        logger.error(f"Error logging API response: {str(e)}")
    
    return response

def mask_sensitive_data(data):
    """
    Mask sensitive data in request/response data
    
    Args:
        data: Dictionary of request/response data
        
    Returns:
        Dictionary with masked sensitive data
    """
    if not data or not isinstance(data, dict):
        return data
    
    # Create a copy to avoid modifying the original
    masked_data = data.copy()
    
    # List of sensitive fields to mask
    sensitive_fields = [
        'password', 'token', 'secret', 'api_key', 'api_secret', 'license_key',
        'access_token', 'refresh_token', 'client_secret', 'private_key'
    ]
    
    # Mask sensitive fields
    for field in sensitive_fields:
        if field in masked_data and masked_data[field]:
            if isinstance(masked_data[field], str) and len(masked_data[field]) > 4:
                # Keep first 2 and last 2 characters, mask the rest
                masked_data[field] = masked_data[field][:2] + '*' * (len(masked_data[field]) - 4) + masked_data[field][-2:]
            else:
                masked_data[field] = '******'
    
    # Recursively mask sensitive data in nested dictionaries
    for key, value in masked_data.items():
        if isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            # Mask sensitive data in list of dictionaries
            masked_data[key] = [
                mask_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
    
    return masked_data

def setup_logging(app):
    """
    Configure logging for the application
    
    Args:
        app: Flask application instance
        
    Returns:
        None
    """
    # Register response logging after_request handler
    app.after_request(log_api_response)
