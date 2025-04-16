"""
Logging Utilities

This module provides consistent logging functionality across the application.
It includes functions to create and configure loggers, custom formatters,
and handlers.
"""

import logging
import os
import sys
import time
from typing import Optional, Union, Dict, Any
from flask import request, g

# Default log levels
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG

# Global log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str, 
    console_level: Optional[int] = None, 
    file_level: Optional[int] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Get or create a logger with the specified name and configuration.
    
    Args:
        name: The logger name, usually the module name
        console_level: The logging level for console output
        file_level: The logging level for file output
        log_file: The path to the log file
        
    Returns:
        A configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set the logger's level to the lowest of all handlers
        min_level = min(
            console_level or DEFAULT_CONSOLE_LEVEL,
            file_level or DEFAULT_FILE_LEVEL
        )
        logger.setLevel(min_level)
        
        # Create formatters
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level or DEFAULT_CONSOLE_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if requested
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(file_level or DEFAULT_FILE_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


def configure_app_logger(app: Any) -> None:
    """
    Configure Flask application logging.
    
    Args:
        app: The Flask application instance
    """
    # Configure Flask app logger
    app.logger.handlers.clear()
    
    # Get root logger and copy its configuration to app.logger
    root_logger = logging.getLogger()
    app.logger.setLevel(root_logger.level)
    
    for handler in root_logger.handlers:
        app.logger.addHandler(handler)


def log_request(logger: logging.Logger, request: Any, response: Any, duration_ms: float) -> None:
    """
    Log HTTP request details.
    
    Args:
        logger: The logger to use
        request: The Flask request object
        response: The Flask response object
        duration_ms: Request processing duration in milliseconds
    """
    # Extract relevant information
    method = request.method
    path = request.path
    status = response.status_code
    
    logger.info(f"API Response: {method} {path} - Status: {status}, Duration: {int(duration_ms)}ms")
    
    # Log request details at debug level
    if logger.isEnabledFor(logging.DEBUG):
        headers = dict(request.headers)
        # Remove sensitive information
        if 'Authorization' in headers:
            headers['Authorization'] = '[REDACTED]'
        if 'Cookie' in headers:
            headers['Cookie'] = '[REDACTED]'
            
        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request args: {dict(request.args)}")


def log_error(
    logger: logging.Logger, 
    error: Exception, 
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with context.
    
    Args:
        logger: The logger to use
        error: The exception to log
        context: Additional context information
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    log_entry = f"Error: {error_type} - {error_message}"
    
    if context:
        # Sanitize context data
        safe_context = {k: v for k, v in context.items()}
        for sensitive_key in ['password', 'token', 'secret', 'key', 'credential']:
            for k in list(safe_context.keys()):
                if sensitive_key in k.lower():
                    safe_context[k] = '[REDACTED]'
        
        log_entry += f" | Context: {safe_context}"
    
    logger.error(log_entry, exc_info=True)


def setup_logging(app: Any) -> None:
    """
    Set up logging for the Flask application.
    
    This function configures request logging middleware and other logging
    features for the Flask application.
    
    Args:
        app: The Flask application instance
    """
    # Configure app logger
    configure_app_logger(app)
    
    # Set up request logging
    @app.before_request
    def before_request():
        # Store request start time
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Skip logging for static files
        if '/static/' in request.path:
            return response
            
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
        else:
            duration_ms = 0
            
        # Log the request
        logger = get_logger('flask_backend.utils.logger')
        log_request(logger, request, response, duration_ms)
        
        return response
    
    # Set up error logging
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error
        logger = get_logger('flask_backend.utils.logger')
        context = {
            'url': request.url if request else 'Unknown',
            'method': request.method if request else 'Unknown',
            'user_id': g.user.id if hasattr(g, 'user') and g.user else None,
            'tenant_id': g.tenant_id if hasattr(g, 'tenant_id') else None
        }
        log_error(logger, error, context)
        
        # Pass through to the default error handler
        return app.handle_exception(error)