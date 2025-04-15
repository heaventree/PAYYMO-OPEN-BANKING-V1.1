"""
Tenant Isolation Service

This module provides tenant isolation and management functions for the multi-tenant architecture.
"""
import logging
import threading
from functools import wraps
from flask import request, g, abort
from sqlalchemy.orm import Query
from sqlalchemy import or_
from flask_backend.app import db
from flask_backend.models import WhmcsInstance

# Thread-local storage for tenant context
_tenant_context = threading.local()

# Logger
logger = logging.getLogger(__name__)

class TenantService:
    """Service for managing tenant isolation and security"""
    
    def __init__(self):
        """Initialize the tenant isolation service"""
        pass
    
    def get_current_tenant(self):
        """
        Get the current tenant from context
        
        Returns:
            Current tenant ID or None if no tenant is set
        """
        return getattr(_tenant_context, 'tenant_id', None)
    
    def set_current_tenant(self, tenant_id):
        """
        Set the current tenant in context
        
        Args:
            tenant_id: ID of the tenant to set
        """
        _tenant_context.tenant_id = tenant_id
        logger.debug(f"Set current tenant: {tenant_id}")
    
    def clear_current_tenant(self):
        """Clear the current tenant from context"""
        if hasattr(_tenant_context, 'tenant_id'):
            delattr(_tenant_context, 'tenant_id')
        logger.debug("Cleared current tenant")
    
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
            bank_accounts = db.session.query(BankConnection.account_id).filter(
                BankConnection.whmcs_instance_id == tenant_id
            ).subquery()
            
            # Filter transactions by account_id
            return query.filter(model.account_id.in_(bank_accounts))
        
        # For Stripe payments, need to join through connections
        if model.__name__ == 'StripePayment':
            # Subquery to get all stripe_connection_ids for this tenant
            from flask_backend.models import StripeConnection
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