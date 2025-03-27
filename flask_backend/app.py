import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set default paths for GoCardless webhook certificates
DEFAULT_CERT_PATH = os.path.join(os.path.dirname(__file__), 'certs', 'webhook_cert.pem')
DEFAULT_KEY_PATH = os.path.join(os.path.dirname(__file__), 'certs', 'webhook_key.pem')

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Set secret key from environment variable or use a default for development
app.secret_key = os.environ.get("SESSION_SECRET", "payymo_dev_secret_key")

# Configure database - PostgreSQL in production, SQLite for development
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///payymo.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure GoCardless settings
app.config["GOCARDLESS_WEBHOOK_CERT_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_CERT_PATH", DEFAULT_CERT_PATH)
app.config["GOCARDLESS_WEBHOOK_KEY_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_KEY_PATH", DEFAULT_KEY_PATH)
app.config["GOCARDLESS_SANDBOX_MODE"] = os.environ.get("GOCARDLESS_SANDBOX_MODE", "true")

# Log GoCardless configuration
logger.info(f"GoCardless webhook certificate path: {app.config['GOCARDLESS_WEBHOOK_CERT_PATH']}")
logger.info(f"GoCardless webhook key path: {app.config['GOCARDLESS_WEBHOOK_KEY_PATH']}")
logger.info(f"GoCardless sandbox mode: {app.config['GOCARDLESS_SANDBOX_MODE']}")

# Initialize the database with the app
db.init_app(app)

# Import routes
with app.app_context():
    # Import routes and models here to avoid circular imports
    from flask_backend.routes import register_blueprints
    from flask_backend.routes_testing import *
    from flask_backend.routes_test_data import *
    from flask_backend.routes_steex import *  # Import Steex dashboard routes
    from flask_backend.routes_fresh import *  # Import Fresh Steex dashboard routes
    import flask_backend.models
    
    # Register blueprints
    register_blueprints(app)
    
    # Create all database tables
    db.create_all()

    # Add root route for redirection
    from flask import redirect, url_for, session
    
    @app.route('/')
    def index():
        """Root route redirects to the Steex dashboard as the default dashboard"""
        # Redirect directly to the Steex dashboard since it's more stable
        return redirect(url_for('steex_dashboard'))
    
    logger.info("Flask backend started successfully")
