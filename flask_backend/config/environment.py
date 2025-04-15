"""
Environment Configuration Module
-------------------------------

Centralizes environment detection and configuration to ensure consistent behavior
across all application components. This module provides:

1. Unified environment detection (dev, test, production)
2. Environment-specific configuration factories
3. Consistent behavior patterns for different environments
4. Single source of truth for environment-related decisions

All other modules should use this module instead of directly checking environment
variables or implementing their own environment-specific logic.
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    
    @classmethod
    def from_string(cls, env_string: Optional[str]) -> 'Environment':
        """Convert string to Environment enum"""
        if not env_string:
            return cls.DEVELOPMENT
            
        # Standardize input
        env_string = env_string.lower().strip()
        
        # Map common variations to standard names
        env_map = {
            "dev": cls.DEVELOPMENT,
            "development": cls.DEVELOPMENT,
            "test": cls.TESTING,
            "testing": cls.TESTING,
            "stage": cls.STAGING,
            "staging": cls.STAGING,
            "prod": cls.PRODUCTION,
            "production": cls.PRODUCTION
        }
        
        return env_map.get(env_string, cls.DEVELOPMENT)

# Detect current environment
current_env_str = os.environ.get('ENVIRONMENT') or os.environ.get('FLASK_ENV') or 'development'
CURRENT_ENV = Environment.from_string(current_env_str)

# Boolean flags for convenience
IS_DEVELOPMENT = CURRENT_ENV == Environment.DEVELOPMENT
IS_TESTING = CURRENT_ENV == Environment.TESTING
IS_STAGING = CURRENT_ENV == Environment.STAGING
IS_PRODUCTION = CURRENT_ENV == Environment.PRODUCTION

# Production-like environments (stricter validation, no fallbacks)
IS_PRODUCTION_LIKE = CURRENT_ENV in (Environment.PRODUCTION, Environment.STAGING)

# Log the detected environment
logger.info(f"Running in {CURRENT_ENV.value.upper()} environment")

# Default database configuration
def get_database_config() -> Dict[str, Any]:
    """Get environment-specific database configuration"""
    # Base configuration
    config = {
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    }
    
    # Environment-specific database URI
    if IS_PRODUCTION_LIKE or IS_TESTING:
        # Use PostgreSQL for production, staging and testing
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set, using fallback SQLite database in production environment")
            db_url = "sqlite:///payymo.db"
    else:
        # Use SQLite for development
        db_url = os.environ.get("DATABASE_URL", "sqlite:///payymo.db")
    
    config["SQLALCHEMY_DATABASE_URI"] = db_url
    return config

# Security configuration
def get_security_config() -> Dict[str, Any]:
    """Get environment-specific security configuration"""
    # Session expiration time (default: 12 hours)
    session_expiration = int(os.environ.get('SESSION_EXPIRATION', 43200))
    
    # JWT expiration time (default: 1 hour)
    jwt_expiration = int(os.environ.get('JWT_EXPIRATION', 3600))
    
    # Base configuration
    config = {
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": 'Lax',
        "PERMANENT_SESSION_LIFETIME": session_expiration,
        "JWT_EXPIRATION": jwt_expiration,
        "PASSWORD_MIN_LENGTH": 12,
        "CSRF_EXPIRATION": 3600,  # 1 hour in seconds
        "API_RATE_LIMIT": 100,  # Requests per minute
        "STRICT_SLASHES": False
    }
    
    # Environment-specific settings
    if IS_PRODUCTION_LIKE:
        # Stricter security for production environments
        config.update({
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_SAMESITE": 'Strict',
            "REMEMBER_COOKIE_SECURE": True,
            "REMEMBER_COOKIE_HTTPONLY": True,
            "REMEMBER_COOKIE_SAMESITE": 'Strict',
        })
    else:
        # More lenient for development
        config.update({
            "SESSION_COOKIE_SECURE": False,
            "DEBUG": True,
            "TESTING": IS_TESTING,
        })
    
    return config

# Get all application configuration
def get_app_config() -> Dict[str, Any]:
    """Get complete environment-specific application configuration"""
    config = {}
    
    # Add database config
    config.update(get_database_config())
    
    # Add security config
    config.update(get_security_config())
    
    # Add secrets/vault config
    config.update({
        "SECRETS_PROVIDERS": os.environ.get('SECRETS_PROVIDERS', 'env,file'),
        "SECRETS_FILE": os.environ.get('SECRETS_FILE', '.secrets.json'),
        "PRELOAD_SECRETS": True,
    })
    
    # Add GoCardless config
    sandbox_mode = not IS_PRODUCTION
    if os.environ.get('GOCARDLESS_SANDBOX_MODE') is not None:
        # Override with explicit setting if provided
        sandbox_mode = os.environ.get('GOCARDLESS_SANDBOX_MODE').lower() == 'true'
    
    config.update({
        "GOCARDLESS_SANDBOX_MODE": sandbox_mode,
        "GOCARDLESS_WEBHOOK_CERT_PATH": os.environ.get('GOCARDLESS_WEBHOOK_CERT_PATH'),
        "GOCARDLESS_WEBHOOK_KEY_PATH": os.environ.get('GOCARDLESS_WEBHOOK_KEY_PATH'),
    })
    
    return config

# Default configuration for secrets service
def get_secrets_config() -> Dict[str, Any]:
    """Get environment-specific secrets configuration"""
    return {
        "allow_fallbacks": not IS_PRODUCTION_LIKE,
        "preload_secrets": True,
        "strict_validation": IS_PRODUCTION_LIKE,
    }