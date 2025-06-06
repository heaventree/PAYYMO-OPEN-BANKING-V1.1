"""
Tenant Middleware

This module provides middleware for tenant isolation in the multi-tenant architecture.
"""
import logging
from functools import wraps
from flask import request, g
from sqlalchemy.event import listen
from sqlalchemy.orm import Query
from flask_backend.app import db
from flask_backend.services.tenant_service import tenant_service

# Logger
logger = logging.getLogger(__name__)

def tenant_middleware():
    """
    Middleware to set tenant context based on request
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            tenant_id = None
            try:
                # Check for domain in request
                domain = None
                if request.is_json:
                    domain = request.json.get('domain')
                elif request.form:
                    domain = request.form.get('domain')
                
                # Check for API key authentication
                api_identifier = request.headers.get('X-API-Identifier')
                
                # If domain is provided, get tenant ID
                if domain:
                    tenant = tenant_service.get_tenant_by_domain(domain)
                    if tenant:
                        tenant_id = tenant.id
                        # Use info level for important operations, debug level creates too much noise
                        if logger.isEnabledFor(logging.INFO):
                            logger.info(f"Using tenant context from domain: {domain} -> {tenant_id}")
                
                # If API key is provided and no tenant ID yet, get tenant ID
                elif api_identifier and not tenant_id:
                    from flask_backend.models import WhmcsInstance
                    tenant = WhmcsInstance.query.filter_by(api_identifier=api_identifier).first()
                    if tenant:
                        tenant_id = tenant.id
                        if logger.isEnabledFor(logging.INFO):
                            logger.info(f"Using tenant context from API key: {api_identifier} -> {tenant_id}")
                
                # Store super admin status in g - use vault service for secure key comparison
                from flask import current_app
                from flask_backend.services.vault_service import vault_service
                
                admin_key_header = request.headers.get('X-Super-Admin-Key')
                super_admin_key = vault_service.get_secret('SUPER_ADMIN_KEY')
                
                if not admin_key_header or not super_admin_key:
                    g.is_super_admin = False
                else:
                    # Use secure comparison from vault service
                    g.is_super_admin = vault_service.secure_compare(admin_key_header, super_admin_key)
                
                # Use tenant context manager to ensure proper cleanup
                with tenant_service.get_tenant_context(tenant_id):
                    # Continue to the route after successful middleware execution
                    return f(*args, **kwargs)
            except Exception as e:
                # Log the error but don't continue - proper error handling is important
                logger.error(f"Error in tenant middleware: {str(e)}")
                
                # Return a proper error response instead of continuing with invalid state
                from flask import jsonify
                from flask_backend.utils.error_handler import APIError, handle_error
                
                # Create an API error that will be handled by the error handler
                api_error = APIError(
                    message="Authentication or tenant context error",
                    status_code=500,
                    error_type="middleware_error",
                    details=str(e)
                )
                
                # Use the central error handler
                return handle_error(api_error)
        
        return wrapped
    
    return decorator

def setup_tenant_filters(app):
    """
    Set up tenant filters for database queries
    
    Args:
        app: Flask application instance
    """
    # Original query method
    original_query = db.session.query
    
    # Override query method to apply tenant filtering
    def tenant_aware_query(*args, **kwargs):
        # Call original query method
        query = original_query(*args, **kwargs)
        
        # Apply tenant filtering if first arg is a model
        if args and hasattr(args[0], '__tablename__'):
            model = args[0]
            tenant_id = tenant_service.get_current_tenant()
            
            if tenant_id:
                # Apply tenant filter
                query = tenant_service.apply_tenant_filter(query, model)
        
        return query
    
    # Replace session query method
    db.session.query = tenant_aware_query
    
    # Define before_compile function
    def before_compile(query):
        # Skip if no _entity_for_tenant
        if not hasattr(query, '_entity_for_tenant'):
            return query
        
        # Skip if no tenant context
        tenant_id = tenant_service.get_current_tenant()
        if not tenant_id:
            return query
        
        # Apply tenant filter
        model = query._entity_for_tenant
        query = tenant_service.apply_tenant_filter(query, model)
        
        return query
    
    # Add event listener for Query execution
    listen(Query, 'before_compile', before_compile, retval=True)
    
    logger.info("Tenant filters set up successfully")