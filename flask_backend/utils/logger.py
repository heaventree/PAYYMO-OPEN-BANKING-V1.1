"""
Request Logger

This module provides logging utilities for the Flask application.
"""
import logging
import time
from datetime import datetime
from flask import request, g, current_app

# Logger
logger = logging.getLogger(__name__)

def setup_logging(app):
    """
    Setup request logging
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def start_timer():
        """Start request timer"""
        g.start_time = time.time()
    
    @app.after_request
    def log_request(response):
        """Log API request and response"""
        # Skip logging for static files
        if request.path.startswith('/static/'):
            return response
        
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration_ms = int((time.time() - g.start_time) * 1000)
        else:
            duration_ms = 0
        
        # Get request data
        request_data = None
        if request.is_json and request.get_data():
            try:
                request_data = request.get_json()
            except Exception:
                request_data = request.get_data(as_text=True)
        elif request.form:
            request_data = dict(request.form)
        
        # Get response data for API endpoints
        response_data = None
        if (
            response.is_json and 
            response.status_code != 204 and
            response.data and
            request.path.startswith('/api/')
        ):
            try:
                response_data = response.get_json()
            except Exception:
                response_data = response.get_data(as_text=True)
        
        # Convert data to strings if needed
        if request_data and not isinstance(request_data, str):
            import json
            try:
                request_data = json.dumps(request_data)
            except Exception as e:
                logger.error(f"Error serializing request data: {str(e)}")
                request_data = str(request_data)
        
        if response_data and not isinstance(response_data, str):
            import json
            try:
                response_data = json.dumps(response_data)
            except Exception as e:
                logger.error(f"Error serializing response data: {str(e)}")
                response_data = str(response_data)
        
        # Log request to console
        logger.info(
            f"API Response: {request.method} {request.path} - "
            f"Status: {response.status_code}, Duration: {duration_ms}ms"
        )
        
        # Log request to database
        try:
            # Import here to avoid circular imports
            from flask_backend.models import ApiLog
            from flask_backend.app import db
            
            log = ApiLog(
                endpoint=request.path,
                method=request.method,
                request_data=request_data,
                response_data=response_data,
                status_code=response.status_code,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string if request.user_agent else None,
                duration_ms=duration_ms,
                created_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging API response: {str(e)}")
            # Don't let logging errors affect the response
            try:
                from flask_backend.app import db
                db.session.rollback()
            except Exception:
                pass
        
        return response
    
    logger.info("Request logging set up successfully")