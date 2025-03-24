"""
Tenant middleware for the multi-tenant SaaS application
Implements the subdomain-based tenant resolution and request context
"""
import logging
from functools import wraps
from flask import request, g, session, redirect, url_for, abort
from flask_backend.models.core import Tenant

# Setup logging
logger = logging.getLogger(__name__)

def get_tenant_from_subdomain(hostname):
    """
    Extract tenant slug from hostname subdomain
    
    Args:
        hostname: The hostname from the request
        
    Returns:
        The tenant slug or None if no subdomain is found
    """
    parts = hostname.split('.')
    
    # Check if we have a subdomain
    if len(parts) < 2:
        return None
        
    # Extract the first part as the subdomain/tenant slug
    subdomain = parts[0]
    
    # Skip common development/staging subdomains
    if subdomain in ['www', 'app', 'api', 'dev', 'staging']:
        return None
        
    return subdomain

def tenant_from_subdomain(f):
    """
    Decorator to resolve tenant from subdomain and add to request context
    
    This decorator:
    1. Extracts the subdomain from the request hostname
    2. Looks up the tenant by slug/subdomain
    3. Adds tenant to request context if found
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract host from request
        hostname = request.headers.get('Host', '')
        
        # Extract tenant slug from subdomain
        tenant_slug = get_tenant_from_subdomain(hostname)
        
        if tenant_slug:
            # Look up tenant by slug
            tenant = Tenant.query.filter_by(slug=tenant_slug).first()
            
            if tenant:
                # Store tenant in request context
                g.tenant = tenant
                g.tenant_id = tenant.id
                
                # Log tenant resolution
                logger.debug(f"Resolved tenant: {tenant.name} (ID: {tenant.id}) from subdomain: {tenant_slug}")
            else:
                # Log tenant not found
                logger.warning(f"Tenant not found for subdomain: {tenant_slug}")
        
        # If no tenant resolved from subdomain, try to get from session
        elif 'tenant_id' in session:
            tenant = Tenant.query.get(session['tenant_id'])
            
            if tenant:
                # Store tenant in request context
                g.tenant = tenant
                g.tenant_id = tenant.id
                
                # Log tenant resolution from session
                logger.debug(f"Resolved tenant from session: {tenant.name} (ID: {tenant.id})")
                
        return f(*args, **kwargs)
    
    return decorated_function

def tenant_required(f):
    """
    Decorator to require a tenant in the request context
    
    This should be used after tenant_from_subdomain to ensure a tenant is available
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant'):
            # No tenant in request context
            if 'user_id' in session:
                # User is logged in, redirect to tenant selection
                return redirect(url_for('auth.select_tenant'))
            else:
                # User is not logged in, redirect to login
                return redirect(url_for('auth.login'))
                
        return f(*args, **kwargs)
    
    return decorated_function

def tenant_header_required(f):
    """
    Decorator to require a tenant header for API requests
    
    This is used for API routes where the tenant is specified in a header
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if tenant is already set in request context (from subdomain or session)
        if hasattr(g, 'tenant') and hasattr(g, 'tenant_id'):
            return f(*args, **kwargs)
            
        # Check for tenant header
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if not tenant_id:
            return abort(400, description="Tenant ID header is required")
            
        try:
            tenant_id = int(tenant_id)
        except ValueError:
            return abort(400, description="Invalid tenant ID format")
            
        # Look up tenant
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return abort(404, description="Tenant not found")
            
        # Store tenant in request context
        g.tenant = tenant
        g.tenant_id = tenant.id
        
        return f(*args, **kwargs)
    
    return decorated_function

def current_tenant():
    """
    Get the current tenant from the request context
    
    Returns:
        The current tenant or None if no tenant is in the request context
    """
    return getattr(g, 'tenant', None)
