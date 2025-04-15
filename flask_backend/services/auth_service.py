"""
Authentication Service

This module provides secure authentication and authorization functionality.
"""
import os
import time
import logging
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, abort, current_app
from flask_backend.models import ApiLog, WhmcsInstance

# Logger
logger = logging.getLogger(__name__)

class AuthService:
    """Service for secure authentication and authorization"""
    
    def __init__(self, app=None):
        """
        Initialize the authentication service
        
        Args:
            app: Flask application instance
        """
        self.secret_key = None
        self.token_expiry = 3600  # 1 hour
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the authentication service with a Flask app
        
        Args:
            app: Flask application instance
        """
        # Get JWT secret key from environment or app secret
        self.secret_key = os.environ.get('JWT_SECRET_KEY', app.secret_key)
        
        # Get token expiry from environment or use default
        self.token_expiry = int(os.environ.get('JWT_TOKEN_EXPIRY', self.token_expiry))
        
        self.initialized = True
        logger.info("Authentication service initialized successfully")
    
    def hash_password(self, password):
        """
        Hash a password for storage
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return generate_password_hash(password)
    
    def verify_password(self, password_hash, password):
        """
        Verify a password against a hash
        
        Args:
            password_hash: Hashed password
            password: Plain text password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        return check_password_hash(password_hash, password)
    
    def generate_api_key(self):
        """
        Generate a secure API key
        
        Returns:
            Secure random API key
        """
        # Generate 32 bytes of random data
        return secrets.token_hex(32)
    
    def generate_token(self, user_id, tenant_id=None, is_admin=False, expiry=None):
        """
        Generate a JWT token
        
        Args:
            user_id: User ID to include in token
            tenant_id: Tenant ID to include in token
            is_admin: Whether the user is an admin
            expiry: Token expiry in seconds
            
        Returns:
            JWT token
        """
        if not self.initialized:
            logger.error("Authentication service not initialized")
            return None
        
        if expiry is None:
            expiry = self.token_expiry
        
        # Current time
        now = datetime.utcnow()
        
        # Create payload
        payload = {
            'sub': str(user_id),
            'iat': now,
            'exp': now + timedelta(seconds=expiry)
        }
        
        # Add tenant ID if provided
        if tenant_id:
            payload['tenant_id'] = str(tenant_id)
        
        # Add admin flag if true
        if is_admin:
            payload['is_admin'] = True
        
        # Generate token
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        return token
    
    def verify_token(self, token):
        """
        Verify a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        if not self.initialized:
            logger.error("Authentication service not initialized")
            return None
        
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    def require_auth(self, admin_required=False):
        """
        Decorator to require authentication
        
        Args:
            admin_required: Whether admin privileges are required
            
        Returns:
            Decorator function
        """
        def decorator(f):
            def wrapped(*args, **kwargs):
                # Get token from Authorization header
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    logger.warning("Missing or invalid Authorization header")
                    abort(401, description="Authentication required")
                
                # Extract token
                token = auth_header.split(' ')[1]
                
                # Verify token
                payload = self.verify_token(token)
                if not payload:
                    logger.warning("Invalid token")
                    abort(401, description="Invalid or expired token")
                
                # Check admin privileges if required
                if admin_required and not payload.get('is_admin', False):
                    logger.warning("Admin privileges required")
                    abort(403, description="Admin privileges required")
                
                # Add user_id to kwargs
                kwargs['user_id'] = payload.get('sub')
                
                # Add tenant_id to kwargs if present
                if 'tenant_id' in payload:
                    kwargs['tenant_id'] = payload.get('tenant_id')
                
                # Log API access
                self._log_api_access()
                
                return f(*args, **kwargs)
            
            # Set wrapper attributes
            wrapped.__name__ = f.__name__
            wrapped.__doc__ = f.__doc__
            
            return wrapped
        
        return decorator
    
    def verify_webhook_signature(self, signature, payload, secret):
        """
        Verify a webhook signature
        
        Args:
            signature: Signature to verify
            payload: Raw payload bytes
            secret: Secret key for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not payload or not secret:
            return False
        
        # Convert secret to bytes if needed
        if isinstance(secret, str):
            secret = secret.encode()
        
        # Convert payload to bytes if needed
        if isinstance(payload, str):
            payload = payload.encode()
        
        # Calculate signature
        expected_signature = hmac.new(
            secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(expected_signature, signature)
    
    def _log_api_access(self):
        """Log API access for audit purposes"""
        try:
            # Create log entry
            log = ApiLog(
                endpoint=request.path,
                method=request.method,
                request_data=request.get_data(as_text=True) if request.content_length else None,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status_code=200,  # Presumed success
                duration_ms=0,  # Will be updated later
                created_at=datetime.utcnow()
            )
            
            # Add to database
            from flask_backend.app import db
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging API access: {str(e)}")
    
    def verify_api_credentials(self, tenant_domain, api_identifier, api_secret):
        """
        Verify API credentials for a tenant
        
        Args:
            tenant_domain: Domain of the tenant
            api_identifier: API identifier
            api_secret: API secret
            
        Returns:
            WhmcsInstance if credentials are valid, None otherwise
        """
        # Find tenant
        tenant = WhmcsInstance.query.filter_by(domain=tenant_domain).first()
        
        if not tenant:
            logger.warning(f"Tenant not found: {tenant_domain}")
            return None
        
        # Verify API identifier
        if tenant.api_identifier != api_identifier:
            logger.warning(f"Invalid API identifier for tenant: {tenant_domain}")
            return None
        
        # Verify API secret using constant-time comparison
        if not self._constant_time_compare(tenant.api_secret, api_secret):
            logger.warning(f"Invalid API secret for tenant: {tenant_domain}")
            return None
        
        # Update last seen timestamp
        tenant.last_seen = datetime.utcnow()
        
        try:
            # Save changes
            from flask_backend.app import db
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating tenant last seen: {str(e)}")
        
        return tenant
    
    def _constant_time_compare(self, val1, val2):
        """
        Compare two values using constant-time comparison
        
        Args:
            val1: First value
            val2: Second value
            
        Returns:
            True if values are equal, False otherwise
        """
        if val1 is None or val2 is None:
            return False
        
        # Convert to strings if needed
        if not isinstance(val1, str):
            val1 = str(val1)
        
        if not isinstance(val2, str):
            val2 = str(val2)
        
        # Use hmac.compare_digest for constant-time comparison
        return hmac.compare_digest(val1, val2)

# Create singleton instance
auth_service = AuthService()