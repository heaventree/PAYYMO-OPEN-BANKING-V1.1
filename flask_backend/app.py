import os
import logging
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from functools import wraps
from flask_wtf.csrf import CSRFProtect

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
SUPER_ADMIN_KEY = os.environ.get("SUPER_ADMIN_KEY", "payymo_admin_secret_key")

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Set secret key from environment variable or use a default for development
app.secret_key = os.environ.get("SESSION_SECRET", "payymo_dev_secret_key")

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
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.secret_key)
app.config['JWT_EXPIRATION'] = JWT_EXPIRATION
app.config['ENCRYPTION_KEY'] = os.environ.get('ENCRYPTION_KEY')
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
    import flask_backend.models
    
    # Create all database tables
    db.create_all()
    
    # Register middleware
    register_middleware(app)
    
    logger.info("Flask backend started successfully")
