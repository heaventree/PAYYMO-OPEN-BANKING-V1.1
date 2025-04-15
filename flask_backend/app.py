import os
import logging
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets as python_secrets  # renamed to avoid conflict

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import centralized environment configuration
from flask_backend.config import (
    CURRENT_ENV, 
    IS_DEVELOPMENT,
    IS_PRODUCTION,
    IS_PRODUCTION_LIKE,
    get_app_config
)

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Apply environment-specific configuration
app.config.update(get_app_config())

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Get API rate limit from config (default to 100 if not set)
api_rate_limit = app.config.get('API_RATE_LIMIT', 100)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Use IP address as default limiter key
    default_limits=[f"{api_rate_limit} per minute", "1000 per hour"],
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True,         # Expose rate limit headers
    header_name_mapping={         # Custom headers for rate limit info
        "X-RateLimit-Limit": "X-RateLimit-Limit",
        "X-RateLimit-Remaining": "X-RateLimit-Remaining",
        "X-RateLimit-Reset": "X-RateLimit-Reset"
    },
    swallow_errors=True           # Ensure app works even if rate limiter fails
)

# Setup secure headers
@app.after_request
def add_security_headers(response):
    """Add security headers to each response"""
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self';"
    )
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Strict Transport Security (only in production)
    if IS_PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Initialize the database with the app
db.init_app(app)

# Initialize the service registry
from flask_backend.services.service_registry import service_registry

# Import all services
from flask_backend.services.vault_service import vault_service
from flask_backend.services.encryption_service import encryption_service
from flask_backend.services.auth_service import auth_service
from flask_backend.services.transaction_service import transaction_service
from flask_backend.services.tenant_service import tenant_service
from flask_backend.middleware.tenant_middleware import setup_tenant_filters

# Register services with dependencies
service_registry.register('vault', vault_service)
service_registry.register('encryption', encryption_service, dependencies=['vault'])
service_registry.register('auth', auth_service, dependencies=['vault', 'encryption'])
service_registry.register('tenant', tenant_service)
service_registry.register('transaction', transaction_service)

# Initialize all services in the correct order
service_registry.initialize(app)

# Set secret key from vault service
app.secret_key = vault_service.get_secret("SESSION_SECRET")
if not app.secret_key and not IS_PRODUCTION:
    logger.warning("SESSION_SECRET not available - generating temporary key for development")
    app.secret_key = vault_service.generate_secure_token()

# Configure security keys required by other services
app.config['JWT_SECRET_KEY'] = vault_service.get_secret('JWT_SECRET_KEY')
app.config['ENCRYPTION_KEY'] = vault_service.get_secret('ENCRYPTION_KEY')
app.config['SUPER_ADMIN_KEY'] = vault_service.get_secret('SUPER_ADMIN_KEY')

# Configure GoCardless webhook certificate paths - no default values
app.config["GOCARDLESS_WEBHOOK_CERT_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_CERT_PATH")
app.config["GOCARDLESS_WEBHOOK_KEY_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_KEY_PATH")

# Log certificate path configuration if available
if app.config["GOCARDLESS_WEBHOOK_CERT_PATH"]:
    logger.info(f"GoCardless webhook certificate path: {app.config['GOCARDLESS_WEBHOOK_CERT_PATH']}")
else:
    logger.warning("GOCARDLESS_WEBHOOK_CERT_PATH not configured")
    
if app.config["GOCARDLESS_WEBHOOK_KEY_PATH"]:
    logger.info(f"GoCardless webhook key path: {app.config['GOCARDLESS_WEBHOOK_KEY_PATH']}")
else:
    logger.warning("GOCARDLESS_WEBHOOK_KEY_PATH not configured")

# In production, having webhook paths is mandatory
if IS_PRODUCTION and (not app.config["GOCARDLESS_WEBHOOK_CERT_PATH"] or not app.config["GOCARDLESS_WEBHOOK_KEY_PATH"]):
    raise RuntimeError("GoCardless webhook certificate paths not configured in production")

# Setup middleware
def register_middleware(app):
    """Register all middleware with the Flask app"""
    # Apply tenant middleware to all routes
    from flask_backend.middleware.tenant_middleware import tenant_middleware
    
    def middleware_wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    
    # Register global request middleware
    app.before_request(lambda: setup_request_context())
    
    # Wrap view functions in the middleware stack
    for endpoint, view_func in app.view_functions.items():
        # Skip static endpoint
        if endpoint == 'static':
            continue
        # Apply tenant middleware
        app.view_functions[endpoint] = tenant_middleware()(view_func)
    
    # Setup tenant filtering for database queries
    setup_tenant_filters(app)
    
    logger.info("All middleware registered successfully")

def setup_request_context():
    """Setup request context for each request"""
    # Set super admin status in g using vault service for secure key comparison
    admin_key_header = request.headers.get('X-Super-Admin-Key')
    super_admin_key = vault_service.get_secret('SUPER_ADMIN_KEY')
    
    if not admin_key_header or not super_admin_key:
        g.is_super_admin = False
    else:
        # Use constant-time comparison from vault service to prevent timing attacks
        g.is_super_admin = vault_service.secure_compare(admin_key_header, super_admin_key)
    
    # Set current tenant in g (for use in templates)
    g.tenant_id = None

# Setup request logging
from flask_backend.utils.logger import setup_logging
setup_logging(app)

# Setup error handlers
from flask_backend.utils.error_handler import register_error_handlers
register_error_handlers(app)

# Import routes
with app.app_context():
    # Import routes and models here to avoid circular imports
    from flask_backend.routes import *
    from flask_backend.routes_testing import *
    from flask_backend.routes_test_data import *
    from flask_backend.routes_security import register_security_routes
    from flask_backend.routes_auth import register_auth_routes
    import flask_backend.models
    
    # Create all database tables
    db.create_all()
    
    # Register middleware
    register_middleware(app)
    
    # Register security routes
    register_security_routes(app)
    
    # Register authentication routes
    register_auth_routes(app)
    
    logger.info("Flask backend started successfully")
