"""
Secrets Service
--------------
A centralized service for managing and accessing secrets and sensitive configuration
values throughout the application. This provides a secure, consistent way to handle
encryption keys, API keys, and other sensitive data.

Key features:
1. Securely store and retrieve sensitive configuration values
2. Centralized validation and access control for secrets
3. Predictable fallbacks and development modes with appropriate warnings
4. Unified logging for security-related operations
"""

import os
import secrets
import logging
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class SecretsService:
    """Service for managing application secrets and sensitive configuration values"""
    
    def __init__(self):
        self._app = None
        self._initialized = False
        self._secrets_cache = {}
        
    def init_app(self, app):
        """Initialize the secrets service with the Flask app"""
        self._app = app
        self._load_secrets()
        self._validate_critical_secrets()
        self._initialized = True
        logger.info("Secrets service initialized")
        
    def _load_secrets(self):
        """Load secrets from environment variables and app config"""
        if not self._app:
            logger.error("Cannot load secrets without app context")
            return
            
        # Determine environment
        self.is_production = os.environ.get('ENVIRONMENT') == 'production'
        
        # Load predefined secrets
        self._secrets_cache = {
            'JWT_SECRET_KEY': self._app.config.get('JWT_SECRET_KEY'),
            'ENCRYPTION_KEY': self._app.config.get('ENCRYPTION_KEY'),
            'SUPER_ADMIN_KEY': self._app.config.get('SUPER_ADMIN_KEY'),
            'SESSION_SECRET': self._app.secret_key,
        }
        
    def _validate_critical_secrets(self):
        """Validate that all critical secrets are available"""
        critical_secrets = ['JWT_SECRET_KEY', 'ENCRYPTION_KEY', 'SUPER_ADMIN_KEY', 'SESSION_SECRET']
        
        for secret_name in critical_secrets:
            if not self._secrets_cache.get(secret_name):
                if self.is_production:
                    logger.critical(f"{secret_name} is not set in production environment")
                else:
                    logger.warning(f"{secret_name} is not set in development environment")
    
    def get_secret(self, name: str, default: Any = None) -> Union[str, bytes, None]:
        """
        Get a secret value by name
        
        Args:
            name: Name of the secret to retrieve
            default: Optional default value if secret is not found
            
        Returns:
            The secret value or default
        """
        if not self._initialized:
            logger.error("Secrets service not initialized")
            return default
            
        # First check cache
        secret = self._secrets_cache.get(name)
        if secret:
            return secret
            
        # Then check app config
        if self._app and name in self._app.config:
            self._secrets_cache[name] = self._app.config[name]
            return self._app.config[name]
            
        # Finally check environment
        env_secret = os.environ.get(name)
        if env_secret:
            self._secrets_cache[name] = env_secret
            return env_secret
            
        # Not found
        logger.warning(f"Secret {name} not found")
        return default
        
    def set_secret(self, name: str, value: Any) -> bool:
        """
        Set a secret value (only for development/testing)
        
        Args:
            name: Name of the secret to set
            value: Value to set
            
        Returns:
            Success status
        """
        if self.is_production:
            logger.error("Cannot set secrets at runtime in production")
            return False
            
        if not self._initialized:
            logger.error("Secrets service not initialized")
            return False
            
        self._secrets_cache[name] = value
        
        # Also set in app config
        if self._app:
            self._app.config[name] = value
            
        return True
        
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure token
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            A secure hex token string
        """
        return secrets.token_hex(length)
        
    def rotate_secret(self, name: str) -> Optional[str]:
        """
        Rotate a secret to a new value (development only)
        
        Args:
            name: Name of the secret to rotate
            
        Returns:
            The new secret value or None if failed
        """
        if self.is_production:
            logger.error("Cannot rotate secrets at runtime in production")
            return None
            
        if not self._initialized:
            logger.error("Secrets service not initialized")
            return None
            
        # Generate a new secret
        new_secret = self.generate_secure_token()
        
        # Store it
        success = self.set_secret(name, new_secret)
        if success:
            logger.info(f"Secret {name} rotated successfully")
            return new_secret
        else:
            logger.error(f"Failed to rotate secret {name}")
            return None

# Singleton instance
secrets_service = SecretsService()