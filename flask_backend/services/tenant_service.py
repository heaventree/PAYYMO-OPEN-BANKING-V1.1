"""
Tenant Isolation Service

This module provides tenant isolation and management functions for the multi-tenant architecture.
Includes a context manager for efficient tenant context handling.
"""
import logging
import threading
from functools import wraps
from flask import request, g, abort, current_app
from sqlalchemy.orm import Query
from sqlalchemy import or_
from flask_backend.services.base_service import BaseService

# Avoid circular import
# Import models separately
from flask_backend.models import WhmcsInstance

# We'll get db from current_app to avoid circular imports
def get_db():
    """Get SQLAlchemy db instance from current app"""
    if current_app:
        return current_app.extensions['sqlalchemy'].db
    return None

# Thread-local storage for tenant context
_tenant_context = threading.local()

# Logger
logger = logging.getLogger(__name__)

class TenantContextManager:
    """
    Context manager for tenant context to ensure proper cleanup
    and prevent excessive context clearing
    """
    
    def __init__(self, tenant_id=None, tenant_service=None):
        """
        Initialize the tenant context manager
        
        Args:
            tenant_id: Optional tenant ID to set
            tenant_service: Reference to the tenant service
        """
        self.tenant_id = tenant_id
        self.tenant_service = tenant_service
        self.previous_tenant_id = None
        self.debug_enabled = logger.isEnabledFor(logging.DEBUG)
        
    def __enter__(self):
        """Enter the context manager - store previous tenant and set new one"""
        # Store previous tenant ID
        self.previous_tenant_id = self.tenant_service.get_current_tenant()
        
        # Only set if different to minimize unnecessary operations
        if self.tenant_id != self.previous_tenant_id:
            if self.tenant_id is None:
                self.tenant_service.clear_current_tenant(log_operation=False)
                if self.debug_enabled and self.previous_tenant_id is not None:
                    logger.debug(f"Cleared tenant from previous ID: {self.previous_tenant_id}")
            else:
                self.tenant_service.set_current_tenant(self.tenant_id, log_operation=False)
                if self.debug_enabled:
                    logger.debug(f"Set tenant context from {self.previous_tenant_id} to {self.tenant_id}")
                    
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager - restore previous tenant if needed"""
        if exc_type is not None:
            # On exception, ensure tenant context is cleared
            if self.debug_enabled:
                logger.debug(f"Exception in tenant context, clearing: {exc_type}")
            self.tenant_service.clear_current_tenant(log_operation=False)
        elif self.previous_tenant_id != self.tenant_service.get_current_tenant():
            # Only restore if different
            if self.previous_tenant_id is None:
                self.tenant_service.clear_current_tenant(log_operation=False)
                if self.debug_enabled:
                    logger.debug("Restored to no tenant context")
            else:
                self.tenant_service.set_current_tenant(self.previous_tenant_id, log_operation=False)
                if self.debug_enabled:
                    logger.debug(f"Restored tenant context to {self.previous_tenant_id}")
                    
        # Return False to allow exception propagation
        return False

class TenantService(BaseService):
    """Service for managing tenant isolation and security"""
    
    def __init__(self):
        """Initialize the tenant isolation service"""
        self._app = None
        self._initialized = False
        
    def init_app(self, app):
        """Initialize the service with the Flask app"""
        self._app = app
        self._initialized = True
        logger.info("Tenant service initialized successfully")
        
    @property
    def initialized(self):
        """
        Return whether the service is initialized
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized
        
    def health_check(self):
        """
        Return the health status of the service
        
        Returns:
            dict: Health status information with at least 'status' and 'message' keys
        """
        status = "ok" if self._initialized else "error"
        message = f"Tenant service is {'initialized' if self._initialized else 'not initialized'}"
        
        # Count active tenant contexts if possible
        active_tenants = 0
        try:
            if hasattr(_tenant_context, 'tenant_id'):
                active_tenants = 1
        except Exception:
            pass
            
        return {
            "status": status,
            "message": message,
            "details": {
                "active_tenants": active_tenants
            }
        }
    
    def get_current_tenant(self):
        """
        Get the current tenant from context
        
        Returns:
            Current tenant ID or None if no tenant is set
        """
        return getattr(_tenant_context, 'tenant_id', None)
    
    def set_current_tenant(self, tenant_id, log_operation=True, log_level=logging.DEBUG):
        """
        Set the current tenant in context
        
        Args:
            tenant_id: ID of the tenant to set
            log_operation: Whether to log this operation
            log_level: Log level to use (default: DEBUG)
        """
        # Check if tenant is changing
        previous_tenant = getattr(_tenant_context, 'tenant_id', None)
        _tenant_context.tenant_id = tenant_id
        
        # Only log when tenant actually changes and when log level is enabled
        if log_operation and previous_tenant != tenant_id and logger.isEnabledFor(log_level):
            if previous_tenant is None:
                logger.log(log_level, f"Set current tenant: {tenant_id}")
            else:
                logger.log(log_level, f"Changed tenant from {previous_tenant} to {tenant_id}")
        elif log_operation and previous_tenant != tenant_id and log_level == logging.DEBUG and logger.isEnabledFor(logging.INFO):
            # For more critical log levels, use INFO instead if DEBUG is not enabled
            if previous_tenant is None:
                logger.info(f"Set current tenant: {tenant_id}")
            else:
                logger.info(f"Changed tenant from {previous_tenant} to {tenant_id}")
    
    def clear_current_tenant(self, log_operation=True, log_level=logging.DEBUG):
        """
        Clear the current tenant from context
        
        Args:
            log_operation: Whether to log this operation
            log_level: Log level to use (default: DEBUG)
        """
        if hasattr(_tenant_context, 'tenant_id'):
            previous_tenant = getattr(_tenant_context, 'tenant_id', None)
            delattr(_tenant_context, 'tenant_id')
            
            # Only log when actually clearing a tenant and when log level is enabled
            if log_operation and previous_tenant is not None and logger.isEnabledFor(log_level):
                logger.log(log_level, f"Cleared current tenant: {previous_tenant}")
            elif log_operation and previous_tenant is not None and log_level == logging.DEBUG and logger.isEnabledFor(logging.INFO):
                # For more critical log levels, use INFO instead if DEBUG is not enabled
                logger.info(f"Cleared current tenant: {previous_tenant}")
                
    def get_tenant_context(self, tenant_id=None):
        """
        Get a tenant context manager
        
        Args:
            tenant_id: Optional tenant ID to set (or None to clear)
            
        Returns:
            TenantContextManager instance
        """
        return TenantContextManager(tenant_id=tenant_id, tenant_service=self)
    
    def get_tenant_by_domain(self, domain):
        """
        Get tenant by domain
        
        Args:
            domain: Domain of the tenant
            
        Returns:
            WhmcsInstance object or None if not found
        """
        if not domain:
            return None
        
        tenant = WhmcsInstance.query.filter_by(domain=domain).first()
        return tenant
    
    def require_tenant(self, allow_super_admin=False):
        """
        Decorator to require a valid tenant context
        
        Args:
            allow_super_admin: Whether to allow super admin access without tenant context
            
        Returns:
            Decorator function
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Check if tenant is required
                tenant_id = self.get_current_tenant()
                
                if not tenant_id and not (allow_super_admin and g.get('is_super_admin', False)):
                    logger.warning("Tenant required but no tenant context set")
                    abort(403, description="Tenant required")
                
                return f(*args, **kwargs)
            return wrapped
        return decorator
    
    def tenant_from_auth(self):
        """
        Decorator to extract tenant from API key authentication
        
        Returns:
            Decorator function
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Extract API credentials from request
                api_identifier = request.headers.get('X-API-Identifier')
                
                if api_identifier:
                    # Find tenant by API identifier
                    tenant = WhmcsInstance.query.filter_by(api_identifier=api_identifier).first()
                    
                    if tenant:
                        # Set tenant context
                        self.set_current_tenant(tenant.id)
                    else:
                        logger.warning(f"Invalid API identifier: {api_identifier}")
                
                return f(*args, **kwargs)
            return wrapped
        return decorator
    
    def tenant_from_domain(self):
        """
        Decorator to extract tenant from domain parameter
        
        Returns:
            Decorator function
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Extract domain from request
                if request.is_json:
                    domain = request.json.get('domain')
                else:
                    domain = request.form.get('domain')
                
                if domain:
                    # Find tenant by domain
                    tenant = self.get_tenant_by_domain(domain)
                    
                    if tenant:
                        # Set tenant context
                        self.set_current_tenant(tenant.id)
                    else:
                        logger.warning(f"Invalid domain: {domain}")
                
                return f(*args, **kwargs)
            return wrapped
        return decorator
    
    def apply_tenant_filter(self, query, model):
        """
        Apply tenant filter to a query
        
        Args:
            query: SQLAlchemy query to filter
            model: Model class being queried
            
        Returns:
            Filtered query
        """
        tenant_id = self.get_current_tenant()
        
        if not tenant_id:
            # No tenant context, return unchanged query
            return query
        
        # Check if model has whmcs_instance_id column
        if hasattr(model, 'whmcs_instance_id'):
            # Filter by whmcs_instance_id
            return query.filter(model.whmcs_instance_id == tenant_id)
        
        # For bank transactions, need to join through connections
        if model.__name__ == 'Transaction':
            # Subquery to get all account_ids for this tenant
            from flask_backend.models import BankConnection
            # Get db from current app
            db = get_db()
            bank_accounts = db.session.query(BankConnection.account_id).filter(
                BankConnection.whmcs_instance_id == tenant_id
            ).subquery()
            
            # Filter transactions by account_id
            return query.filter(model.account_id.in_(bank_accounts))
        
        # For Stripe payments, need to join through connections
        if model.__name__ == 'StripePayment':
            # Subquery to get all stripe_connection_ids for this tenant
            from flask_backend.models import StripeConnection
            # Get db from current app
            db = get_db()
            stripe_connections = db.session.query(StripeConnection.id).filter(
                StripeConnection.whmcs_instance_id == tenant_id
            ).subquery()
            
            # Filter payments by stripe_connection_id
            return query.filter(model.stripe_connection_id.in_(stripe_connections))
        
        # For other models, return unchanged query
        logger.warning(f"No tenant filter available for model: {model.__name__}")
        return query

# Patch SQLAlchemy Query to support tenant filtering
original_query_init = Query.__init__

def tenant_aware_query_init(self, *args, **kwargs):
    """Initialize query with tenant awareness"""
    # Call original init
    original_query_init(self, *args, **kwargs)
    
    # Store entity for tenant filtering
    if args and hasattr(args[0], '__class__'):
        self._entity_for_tenant = args[0]

def patch_query():
    """Patch SQLAlchemy Query class for tenant isolation"""
    Query.__init__ = tenant_aware_query_init

# Create singleton instance
tenant_service = TenantService()