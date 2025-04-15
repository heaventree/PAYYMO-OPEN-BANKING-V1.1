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

# Security constants
CSRF_EXPIRATION = 3600  # 1 hour in seconds
SESSION_EXPIRATION = 43200  # 12 hours in seconds (reduced from 24 hours)
PASSWORD_MIN_LENGTH = 12
JWT_EXPIRATION = 3600  # 1 hour in seconds
API_RATE_LIMIT = 100  # Requests per minute

# Check if we're in development or production mode
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Configure security settings
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_EXPIRATION
app.config['JWT_EXPIRATION'] = JWT_EXPIRATION
app.config['PASSWORD_MIN_LENGTH'] = PASSWORD_MIN_LENGTH
app.config['CSRF_EXPIRATION'] = CSRF_EXPIRATION
app.config['API_RATE_LIMIT'] = API_RATE_LIMIT
app.config['STRICT_SLASHES'] = False

# Configure Vault Service
app.config['SECRETS_PROVIDERS'] = os.environ.get('SECRETS_PROVIDERS', 'env,file')
app.config['SECRETS_FILE'] = os.environ.get('SECRETS_FILE', '.secrets.json')
app.config['PRELOAD_SECRETS'] = True

# Configure database - PostgreSQL in production, SQLite for development
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///payymo.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Use IP address as default limiter key
    default_limits=[f"{API_RATE_LIMIT} per minute", "1000 per hour"],
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
    if os.environ.get('ENVIRONMENT') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Initialize the database with the app
db.init_app(app)

# Initialize the vault service first (as other services may depend on it)
from flask_backend.services.vault_service import vault_service
vault_service.init_app(app)

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

# Initialize encryption service
from flask_backend.services.encryption_service import encryption_service
encryption_service.init_app(app)

# Initialize authentication service
from flask_backend.services.auth_service import auth_service
auth_service.init_app(app)

# Initialize transaction service (no init_app needed)
from flask_backend.services.transaction_service import transaction_service

# Setup tenant service
from flask_backend.services.tenant_service import tenant_service
from flask_backend.middleware.tenant_middleware import setup_tenant_filters

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
