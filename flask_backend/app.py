import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Set secret key from environment variable or use a default for development
app.secret_key = os.environ.get("SESSION_SECRET", "gocardless_dev_secret_key")

# Configure database - PostgreSQL in production, SQLite for development
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///gocardless.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Import routes
with app.app_context():
    # Import routes and models here to avoid circular imports
    from flask_backend.routes import *
    from flask_backend.routes_testing import *
    import flask_backend.models
    
    # Create all database tables
    db.create_all()

    logger.info("Flask backend started successfully")
