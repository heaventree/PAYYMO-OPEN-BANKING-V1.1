"""
Configuration Package

Contains centralized configuration for the application:
- Environment detection and configuration
- Application settings
- Service configuration
"""

from .environment import (
    CURRENT_ENV,
    Environment,
    IS_DEVELOPMENT,
    IS_TESTING,
    IS_STAGING,
    IS_PRODUCTION,
    IS_PRODUCTION_LIKE,
    get_app_config,
    get_database_config,
    get_security_config,
    get_secrets_config
)