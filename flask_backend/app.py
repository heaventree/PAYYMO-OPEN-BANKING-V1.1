import os
import logging
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set default paths for GoCardless webhook certificates
DEFAULT_CERT_PATH = os.path.join(os.path.dirname(__file__), 'certs', 'webhook_cert.pem')
DEFAULT_KEY_PATH = os.path.join(os.path.dirname(__file__), 'certs', 'webhook_key.pem')

# Security constants
CSRF_EXPIRATION = 3600  # 1 hour in seconds
SESSION_EXPIRATION = 43200  # 12 hours in seconds (reduced from 24 hours)
PASSWORD_MIN_LENGTH = 12
JWT_EXPIRATION = 3600  # 1 hour in seconds
API_RATE_LIMIT = 100  # Requests per minute
# Check if we're in development or production mode
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'

# In production, no default values for security keys
# In development, we can use generated keys with warnings
SUPER_ADMIN_KEY = os.environ.get("SUPER_ADMIN_KEY")
if not SUPER_ADMIN_KEY:
    if IS_PRODUCTION:
        logger.critical("SUPER_ADMIN_KEY not set in production environment!")
    else:
        import secrets
        logger.warning("SUPER_ADMIN_KEY not set - using temporary key for development only!")
        logger.warning("This is insecure for production! Set proper keys before launch as per PRE_LAUNCH_SECURITY_KEYS.md")
        SUPER_ADMIN_KEY = secrets.token_hex(16)  # Generate a temporary key for development

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Set secret key from environment variable - no default for security
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key and os.environ.get('ENVIRONMENT') != 'production':
    logger.warning("SESSION_SECRET not set - using temporary random key for development only!")
    app.secret_key = os.urandom(32)  # Generate random key for development

# Configure database - PostgreSQL in production, SQLite for development
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///payymo.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure GoCardless webhook certificate paths
app.config["GOCARDLESS_WEBHOOK_CERT_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_CERT_PATH", DEFAULT_CERT_PATH)
app.config["GOCARDLESS_WEBHOOK_KEY_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_KEY_PATH", DEFAULT_KEY_PATH)

# Log certificate path configuration
logger.info(f"GoCardless webhook certificate path: {app.config['GOCARDLESS_WEBHOOK_CERT_PATH']}")
logger.info(f"GoCardless webhook key path: {app.config['GOCARDLESS_WEBHOOK_KEY_PATH']}")

# Configure security settings
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENVIRONMENT') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_EXPIRATION
# Use environment variable for JWT_SECRET_KEY, or generate one if in development
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
if not app.config['JWT_SECRET_KEY']:
    if os.environ.get('ENVIRONMENT') == 'production':
        logger.critical("JWT_SECRET_KEY not set in production environment!")
    else:
        logger.warning("JWT_SECRET_KEY not set - using a generated key for development only!")
        # Generate a random key for development
        import secrets
        app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_EXPIRATION'] = JWT_EXPIRATION

# Handle encryption key
app.config['ENCRYPTION_KEY'] = os.environ.get('ENCRYPTION_KEY')
if not app.config['ENCRYPTION_KEY']:
    if os.environ.get('ENVIRONMENT') == 'production':
        logger.critical("ENCRYPTION_KEY not set in production environment!")
    else:
        logger.warning("ENCRYPTION_KEY not set - using a generated key for development only!")
        import secrets
        app.config['ENCRYPTION_KEY'] = secrets.token_hex(32)

app.config['SUPER_ADMIN_KEY'] = SUPER_ADMIN_KEY
app.config['STRICT_SLASHES'] = False

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

# Initialize the secrets service first (as other services may depend on it)
from flask_backend.services.secrets_service import secrets_service
secrets_service.init_app(app)

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
    
    # Register teardown handler to clear tenant context
    @app.teardown_request
    def clear_tenant_context(exception=None):
        """Clear tenant context after each request"""
        from flask_backend.services.tenant_service import tenant_service
        tenant_service.clear_current_tenant()
    
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
    # Set super admin status in g
    g.is_super_admin = request.headers.get('X-Super-Admin-Key') == app.config['SUPER_ADMIN_KEY']
    
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
    import flask_backend.models
    
    # Create all database tables
    db.create_all()
    
    # Register middleware
    register_middleware(app)
    
    # Register security routes
    register_security_routes(app)
    
    logger.info("Flask backend started successfully")
