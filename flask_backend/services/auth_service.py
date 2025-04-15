"""
Authentication Service

This module provides secure authentication and authorization functionality.
Includes JWT token generation and verification with RS256 signing.
"""
import os
import time
import logging
import secrets
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, abort, current_app, g
from flask_backend.models import ApiLog, WhmcsInstance
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

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
        self.private_key = None
        self.public_key = None
        self.token_expiry = 3600  # 1 hour
        self.token_audience = None
        self.token_issuer = None
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the authentication service with a Flask app
        
        Args:
            app: Flask application instance
        """
        # Get JWT keys from secrets service
        from flask_backend.services.secrets_service import secrets_service
        
        # Set token metadata for better security
        self.token_audience = app.config.get('JWT_AUDIENCE', 'payymo-api')
        self.token_issuer = app.config.get('JWT_ISSUER', 'payymo-auth')
        
        # Try to get RSA keys from secrets service
        self.private_key_pem = secrets_service.get_secret('JWT_PRIVATE_KEY')
        self.public_key_pem = secrets_service.get_secret('JWT_PUBLIC_KEY')
        
        # Generate new RSA keys if not found
        if not self.private_key_pem or not self.public_key_pem:
            if os.environ.get('ENVIRONMENT') == 'production':
                logger.critical("JWT_PRIVATE_KEY or JWT_PUBLIC_KEY not found in production environment")
            else:
                logger.warning("Generating new RSA key pair - not secure for production")
                # Generate new key pair
                self._generate_rsa_keys(secrets_service)
        
        # Load the keys into proper cryptography objects
        if self.private_key_pem:
            try:
                self.private_key = serialization.load_pem_private_key(
                    self.private_key_pem.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
            except Exception as e:
                logger.error(f"Error loading private key: {str(e)}")
                if os.environ.get('ENVIRONMENT') != 'production':
                    # Regenerate keys in development only
                    logger.warning("Regenerating RSA keys due to error")
                    self._generate_rsa_keys(secrets_service)
                    
        if self.public_key_pem:
            try:
                self.public_key = serialization.load_pem_public_key(
                    self.public_key_pem.encode('utf-8'),
                    backend=default_backend()
                )
            except Exception as e:
                logger.error(f"Error loading public key: {str(e)}")
                if os.environ.get('ENVIRONMENT') != 'production':
                    # Regenerate keys in development only
                    logger.warning("Regenerating RSA keys due to error")
                    self._generate_rsa_keys(secrets_service)
        
        # Get token expiry from app config or use default
        self.token_expiry = int(app.config.get('JWT_EXPIRATION', self.token_expiry))
        
        # Store a successful initialization state
        if self.private_key and self.public_key:
            self.initialized = True
            logger.info("Authentication service initialized successfully with RS256 keys")
        else:
            logger.critical("Failed to initialize authentication service properly")
    
    def _generate_rsa_keys(self, secrets_service):
        """
        Generate a new RSA key pair and store in secrets service
        
        Args:
            secrets_service: Secrets service instance
        """
        # Generate a new private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Get the public key
        public_key = private_key.public_key()
        
        # Serialize private key to PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Serialize public key to PEM format
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Store in secrets service
        secrets_service.set_secret('JWT_PRIVATE_KEY', private_key_pem)
        secrets_service.set_secret('JWT_PUBLIC_KEY', public_key_pem)
        
        # Update instance variables
        self.private_key = private_key
        self.public_key = public_key
        self.private_key_pem = private_key_pem
        self.public_key_pem = public_key_pem
        
        logger.info("Generated new RSA key pair for JWT authentication")
    
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
        
    def dummy_password_check(self):
        """
        Perform a dummy password check to prevent timing attacks
        
        This method simulates the time it would take to verify a password
        to prevent timing attacks that could reveal if a user exists.
        It performs the same operations as a real password check but with
        dummy values that always return False.
        
        Returns:
            Always False
        """
        # Create a dummy password and hash of similar complexity to real ones
        dummy_hash = generate_password_hash("dummy_password")
        # Perform the check, which will always return False but take similar time
        return check_password_hash(dummy_hash, "wrong_password")
    
    def generate_api_key(self):
        """
        Generate a secure API key
        
        Returns:
            Secure random API key
        """
        # Generate 32 bytes of random data
        return secrets.token_hex(32)
    
    def generate_token(self, user_id, tenant_id=None, is_admin=False, expiry=None, permissions=None):
        """
        Generate a JWT token using RS256 asymmetric signing
        
        Args:
            user_id: User ID to include in token
            tenant_id: Tenant ID to include in token
            is_admin: Whether the user is an admin
            expiry: Token expiry in seconds
            permissions: List of permissions granted to the user
            
        Returns:
            JWT token
        """
        if not self.initialized or not self.private_key:
            logger.error("Authentication service not initialized with proper keys")
            return None
        
        if expiry is None:
            expiry = self.token_expiry
        
        # Current time
        now = datetime.utcnow()
        
        # Generate a unique token ID (jti claim)
        token_id = str(uuid.uuid4())
        
        # Create payload with standard claims
        payload = {
            'iss': self.token_issuer,        # Issuer
            'aud': self.token_audience,      # Audience
            'jti': token_id,                 # JWT ID (unique identifier)
            'sub': str(user_id),             # Subject (user ID)
            'iat': int(now.timestamp()),     # Issued at time (as UNIX timestamp)
            'exp': int((now + timedelta(seconds=expiry)).timestamp()),  # Expiration time
            'nbf': int(now.timestamp())      # Not valid before (as UNIX timestamp)
        }
        
        # Add tenant ID if provided
        if tenant_id:
            payload['tenant_id'] = str(tenant_id)
        
        # Add admin flag if true
        if is_admin:
            payload['is_admin'] = True
        
        # Add permissions if provided
        if permissions:
            payload['permissions'] = permissions
        
        # Generate token using the private key with RS256 algorithm
        try:
            token = jwt.encode(payload, self.private_key_pem, algorithm='RS256')
            return token
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            return None
    
    def verify_token(self, token):
        """
        Verify a JWT token using RS256 asymmetric verification
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        if not self.initialized or not self.public_key:
            logger.error("Authentication service not initialized with proper keys")
            return None
        
        try:
            # Verify token with proper audience and issuer validation
            options = {
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
                'require_exp': True,
                'require_iat': True,
                'require_nbf': True
            }
            
            # Decode and verify token using the public key
            payload = jwt.decode(
                token, 
                self.public_key_pem, 
                algorithms=['RS256'],
                audience=self.token_audience,
                issuer=self.token_issuer,
                options=options
            )
            
            # Store the token in the request context for later use
            g.jwt_payload = payload
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidAudienceError:
            logger.warning("Token has an invalid audience")
            return None
        except jwt.InvalidIssuerError:
            logger.warning("Token has an invalid issuer")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
    
    def require_auth(self, admin_required=False, required_permissions=None):
        """
        Decorator to require authentication and check permissions
        
        Args:
            admin_required: Whether admin privileges are required
            required_permissions: List of permissions required for the endpoint
            
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
                
                # Check token revocation
                if self._is_token_revoked(payload.get('jti')):
                    logger.warning("Token has been revoked")
                    abort(401, description="Token has been revoked")
                
                # Check admin privileges if required
                if admin_required and not payload.get('is_admin', False):
                    logger.warning("Admin privileges required")
                    abort(403, description="Admin privileges required")
                
                # Check permissions if required
                if required_permissions:
                    user_permissions = payload.get('permissions', [])
                    
                    # Check if the user has all required permissions
                    if not all(perm in user_permissions for perm in required_permissions):
                        logger.warning(f"Missing required permissions: {required_permissions}")
                        abort(403, description="Insufficient permissions")
                
                # Store payload in request context for use in the route function
                g.jwt_payload = payload
                g.current_user = payload
                
                # Set user ID in context
                g.user_id = payload.get('sub')
                
                # Set tenant ID in context if present
                if 'tenant_id' in payload:
                    g.tenant_id = payload.get('tenant_id')
                
                # Log API access
                self._log_api_access()
                
                # Call the route function without passing extra parameters
                return f(*args, **kwargs)
            
            # Set wrapper attributes
            wrapped.__name__ = f.__name__
            wrapped.__doc__ = f.__doc__
            
            return wrapped
        
        return decorator
        
    def _is_token_revoked(self, token_id):
        """
        Check if a token has been revoked
        
        Args:
            token_id: Unique JWT ID (jti) to check
            
        Returns:
            True if the token has been revoked, False otherwise
        """
        if not token_id:
            return False
            
        # Import here to avoid circular imports
        from flask_backend.models import TokenRevocation
        
        # Check if token exists in revocation list
        revocation = TokenRevocation.query.filter_by(jti=token_id).first()
        
        # Return True if token is found in revocation list
        return revocation is not None
        
    def revoke_token(self, token_id, reason=None, user_id=None):
        """
        Revoke a token by its ID
        
        Args:
            token_id: Unique JWT ID (jti) to revoke
            reason: Optional reason for revocation
            user_id: Optional user ID associated with token
            
        Returns:
            True if revocation was successful, False otherwise
        """
        if not token_id:
            return False
            
        from flask_backend.models import TokenRevocation
        from flask_backend.app import db
        
        try:
            # Check if token is already revoked
            existing = TokenRevocation.query.filter_by(jti=token_id).first()
            if existing:
                logger.warning(f"Token {token_id} already revoked")
                return True
            
            # Create a new token revocation record
            token_revocation = TokenRevocation(
                jti=token_id,
                user_id=user_id,
                reason=reason or 'User logout',
                token_type='access',  # Default to access token
                revoked_at=datetime.utcnow(),
                # We would normally calculate expires_at from the token, but for simplicity
                # we'll set it to 24 hours from now
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # Save to database
            db.session.add(token_revocation)
            db.session.commit()
            
            logger.info(f"Token {token_id} revoked. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            db.session.rollback()
            return False
        
    def generate_refresh_token(self, user_id, token_id=None):
        """
        Generate a refresh token for token rotation
        
        Args:
            user_id: User ID to include in token
            token_id: Optional original token ID to link for auditing
            
        Returns:
            Refresh token
        """
        if not self.initialized or not self.private_key:
            logger.error("Authentication service not initialized with proper keys")
            return None
            
        # Current time
        now = datetime.utcnow()
        
        # Create a longer expiry for refresh tokens
        refresh_expiry = self.token_expiry * 24  # 24x longer than access token
        
        # Generate a unique token ID (jti claim)
        refresh_token_id = str(uuid.uuid4())
        
        # Create payload with standard claims for a refresh token
        payload = {
            'iss': self.token_issuer,
            'aud': f"{self.token_audience}-refresh",  # Different audience for refresh tokens
            'jti': refresh_token_id,
            'sub': str(user_id),
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=refresh_expiry)).timestamp()),
            'nbf': int(now.timestamp()),
            'token_type': 'refresh'  # Mark this explicitly as a refresh token
        }
        
        # Link to original token if provided
        if token_id:
            payload['orig_jti'] = token_id
            
        # Generate token using the private key with RS256 algorithm
        try:
            token = jwt.encode(payload, self.private_key_pem, algorithm='RS256')
            return token
        except Exception as e:
            logger.error(f"Error generating refresh token: {str(e)}")
            return None
            
    def refresh_access_token(self, refresh_token):
        """
        Generate a new access token from a refresh token
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            New access token or None if invalid
        """
        # Verify the refresh token
        try:
            # Special options for refresh tokens
            options = {
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
                'require_exp': True,
                'require_iat': True,
                'require_nbf': True
            }
            
            # Decode and verify refresh token using the public key
            payload = jwt.decode(
                refresh_token, 
                self.public_key_pem, 
                algorithms=['RS256'],
                audience=f"{self.token_audience}-refresh",
                issuer=self.token_issuer,
                options=options
            )
            
            # Verify this is a refresh token
            if payload.get('token_type') != 'refresh':
                logger.warning("Invalid token type for refresh operation")
                return None
                
            # Check if the refresh token is revoked
            if self._is_token_revoked(payload.get('jti')):
                logger.warning("Refresh token has been revoked")
                return None
                
            # Get user ID from the refresh token
            user_id = payload.get('sub')
            if not user_id:
                logger.warning("Refresh token missing user ID")
                return None
                
            # Generate a new access token
            # We would normally load more user data here (tenant, permissions, etc.)
            # Placeholder implementation:
            new_token = self.generate_token(
                user_id=user_id,
                # Additional claims would be loaded from user data in a real implementation
            )
            
            return new_token
            
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidAudienceError:
            logger.warning("Refresh token has an invalid audience")
            return None
        except jwt.InvalidIssuerError:
            logger.warning("Refresh token has an invalid issuer")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            return None
    
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