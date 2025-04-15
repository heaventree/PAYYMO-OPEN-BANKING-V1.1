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
5. Integration with key rotation for secure credential management
6. Graceful degradation in development environments with secure defaults
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
        
        # Initialize key rotation if available
        try:
            from flask_backend.utils.key_rotation import key_rotation_manager
            self.key_rotation_manager = key_rotation_manager
            if not key_rotation_manager.initialized:
                key_rotation_manager.init_app(app)
            self._register_keys_with_rotation_manager()
            self.has_rotation_manager = True
            logger.info("Secrets service initialized with key rotation support")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Key rotation manager not available: {str(e)}")
            self.has_rotation_manager = False
            logger.info("Secrets service initialized without key rotation support")
            
        self._initialized = True
        
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
                    
    def _register_keys_with_rotation_manager(self):
        """Register managed keys with the key rotation manager"""
        if not hasattr(self, 'key_rotation_manager') or not self.key_rotation_manager:
            logger.warning("No key rotation manager available")
            return
            
        # Register keys that have values
        for key_name, key_value in self._secrets_cache.items():
            if key_value:
                if not self.key_rotation_manager.has_key(key_name):
                    self.key_rotation_manager.register_key(key_name, key_value)
                    logger.info(f"Registered {key_name} with key rotation manager")
                else:
                    logger.debug(f"Key {key_name} already registered with rotation manager")
    
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
            
        # First check if we have key rotation manager and it has this key
        if (hasattr(self, 'has_rotation_manager') and self.has_rotation_manager and 
                self.key_rotation_manager.has_key(name)):
            # Get the active key from the rotation manager
            rotated_key = self.key_rotation_manager.get_active_key(name)
            if rotated_key:
                # Update cache with the latest value
                self._secrets_cache[name] = rotated_key
                return rotated_key
            
        # Check cache
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
            
            # Register with rotation manager if available
            if (hasattr(self, 'has_rotation_manager') and self.has_rotation_manager and 
                    not self.key_rotation_manager.has_key(name)):
                self.key_rotation_manager.register_key(name, env_secret)
                logger.info(f"Registered {name} with key rotation manager")
                
            return env_secret
            
        # Not found - log warning
        logger.warning(f"Secret {name} not found")
        return default
        
    def set_secret(self, name: str, value: Any) -> bool:
        """
        Set a secret value
        
        In development mode, this updates the secret value in memory.
        In production mode, this operation is restricted.
        
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
            
        # Update the cache
        self._secrets_cache[name] = value
        
        # Update app config
        if self._app:
            self._app.config[name] = value
            
        # Register with key rotation manager if available
        if (hasattr(self, 'has_rotation_manager') and 
                self.has_rotation_manager):
            if self.key_rotation_manager.has_key(name):
                # Update existing key
                self.key_rotation_manager.rotate_key(name, value)
            else:
                # Register new key
                self.key_rotation_manager.register_key(name, value)
                logger.info(f"Registered {name} with key rotation manager")
            
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
        Rotate a secret to a new value
        
        In development mode, this generates a new secret and updates it in memory.
        In production mode with key rotation manager, this uses the secure key rotation process.
        
        Args:
            name: Name of the secret to rotate
            
        Returns:
            The new secret value or None if failed
        """
        if not self._initialized:
            logger.error("Secrets service not initialized")
            return None
            
        # If we're in production, use the key rotation manager if available
        if self.is_production:
            if hasattr(self, 'has_rotation_manager') and self.has_rotation_manager:
                # Generate a new secret
                new_secret = self.generate_secure_token()
                
                # Use the key rotation manager to handle the rotation
                try:
                    new_version = self.key_rotation_manager.rotate_key(name, new_secret)
                    if new_version:
                        # Update the cache with the new value
                        self._secrets_cache[name] = new_secret
                        if self._app:
                            self._app.config[name] = new_secret
                        logger.info(f"Rotated {name} to version {new_version}")
                        return new_secret
                    else:
                        logger.error(f"Failed to rotate {name}")
                        return None
                except Exception as e:
                    logger.error(f"Error rotating {name}: {str(e)}")
                    return None
            else:
                logger.error("Cannot rotate secrets in production without key rotation manager")
                return None
                
        # For development, just generate and set a new value
        new_secret = self.generate_secure_token()
        
        # Store it
        success = self.set_secret(name, new_secret)
        if success:
            # If we have a key rotation manager, register the new value
            if hasattr(self, 'has_rotation_manager') and self.has_rotation_manager:
                if self.key_rotation_manager.has_key(name):
                    self.key_rotation_manager.rotate_key(name, new_secret)
                else:
                    self.key_rotation_manager.register_key(name, new_secret)
                    
            logger.info(f"Secret {name} rotated successfully")
            return new_secret
        else:
            logger.error(f"Failed to rotate secret {name}")
            return None

# Singleton instance
secrets_service = SecretsService()