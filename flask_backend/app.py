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

# Configure GoCardless webhook certificate paths
app.config["GOCARDLESS_WEBHOOK_CERT_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_CERT_PATH", DEFAULT_CERT_PATH)
app.config["GOCARDLESS_WEBHOOK_KEY_PATH"] = os.environ.get("GOCARDLESS_WEBHOOK_KEY_PATH", DEFAULT_KEY_PATH)

# Log certificate path configuration
logger.info(f"GoCardless webhook certificate path: {app.config['GOCARDLESS_WEBHOOK_CERT_PATH']}")
logger.info(f"GoCardless webhook key path: {app.config['GOCARDLESS_WEBHOOK_KEY_PATH']}")

# Initialize the database with the app
db.init_app(app)

# Import routes
with app.app_context():
    # Import routes and models here to avoid circular imports
    from flask_backend.routes import *
    from flask_backend.routes_testing import *
    from flask_backend.checkout import checkout_bp
    import flask_backend.models
    
    # Register blueprints
    app.register_blueprint(checkout_bp)
    
    # Create all database tables
    db.create_all()

    logger.info("Flask backend started successfully")
