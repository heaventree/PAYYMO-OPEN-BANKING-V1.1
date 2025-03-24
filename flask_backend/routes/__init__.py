"""
Route initialization for the multi-tenant SaaS application
"""
from flask_backend.routes.dashboard import dashboard_bp
from flask_backend.routes.auth import auth_bp
from flask_backend.routes.api import api_bp

# List of all blueprints to register with the app
all_blueprints = [
    dashboard_bp,
    auth_bp,
    api_bp
]

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
    
    # Log registered blueprints
    app.logger.info(f"Registered {len(all_blueprints)} blueprints")
