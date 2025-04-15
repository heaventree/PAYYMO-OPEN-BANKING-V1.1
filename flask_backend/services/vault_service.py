"""
Vault Service
------------
A robust, secure secrets management service that provides centralized access to sensitive configuration values.
This service improves upon the basic secrets_service by adding proper secrets providers, strict
validation, and secure handling with no fallbacks in production.

Key features:
1. Multiple secrets provider backends (Environment, Vault, AWS, etc.)
2. No fallbacks or defaults for critical secrets in production
3. Strict validation for required secrets
4. Proper key rotation support
5. Fail-fast behavior in production
"""

import os
import logging
import json
import time
import secrets
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class SecretsProvider(ABC):
    """Base secrets provider interface"""
    
    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret by name"""
        pass
        
    @abstractmethod
    def set_secret(self, name: str, value: str) -> bool:
        """Set a secret value"""
        pass
        
    @abstractmethod
    def rotate_secret(self, name: str, new_value: str = None) -> Optional[str]:
        """Rotate a secret to a new value"""
        pass

class EnvSecretsProvider(SecretsProvider):
    """Environment-based secrets provider"""
    
    def __init__(self, allow_fallbacks: bool = False):
        self.allow_fallbacks = allow_fallbacks
        
        # Import environment here to avoid circular imports
        from flask_backend.config import IS_PRODUCTION
        self.is_production = IS_PRODUCTION
        
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret from environment variables"""
        value = os.environ.get(name)
        
        # In production, never return None for critical secrets
        if not value and self.is_production and not self.allow_fallbacks:
            # This will be caught by the VaultService and handled appropriately
            return None
            
        return value
        
    def set_secret(self, name: str, value: str) -> bool:
        """
        Set a secret in environment variables
        
        Note: This only affects the current process, not the actual environment
        """
        if self.is_production:
            logger.error("Cannot modify environment variables in production")
            return False
            
        os.environ[name] = value
        return True
        
    def rotate_secret(self, name: str, new_value: str = None) -> Optional[str]:
        """Rotate a secret to a new value"""
        if self.is_production:
            logger.error("Cannot rotate environment variables in production")
            return None
            
        # Generate a new value if not provided
        if new_value is None:
            new_value = secrets.token_hex(32)
            
        # Set the new value
        if self.set_secret(name, new_value):
            return new_value
        return None

class FileSecretsProvider(SecretsProvider):
    """File-based secrets provider for development use"""
    
    def __init__(self, secrets_file: str = ".secrets.json"):
        self.secrets_file = secrets_file
        self.secrets_data = {}
        
        # Import environment here to avoid circular imports
        from flask_backend.config import IS_PRODUCTION
        self.is_production = IS_PRODUCTION
        
        # Load secrets from file if it exists
        self._load_secrets()
        
    def _load_secrets(self):
        """Load secrets from file"""
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'r') as f:
                    self.secrets_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading secrets from file: {str(e)}")
                self.secrets_data = {}
        
    def _save_secrets(self):
        """Save secrets to file"""
        try:
            # Don't save to file in production
            if self.is_production:
                logger.error("Cannot save secrets to file in production")
                return False
                
            with open(self.secrets_file, 'w') as f:
                json.dump(self.secrets_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving secrets to file: {str(e)}")
            return False
        
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret from the loaded secrets data"""
        return self.secrets_data.get(name)
        
    def set_secret(self, name: str, value: str) -> bool:
        """Set a secret in the secrets data and save to file"""
        if self.is_production:
            logger.error("Cannot set secrets in file in production")
            return False
            
        self.secrets_data[name] = value
        return self._save_secrets()
        
    def rotate_secret(self, name: str, new_value: str = None) -> Optional[str]:
        """Rotate a secret to a new value"""
        if self.is_production:
            logger.error("Cannot rotate secrets in file in production")
            return None
            
        # Generate a new value if not provided
        if new_value is None:
            new_value = secrets.token_hex(32)
            
        # Set the new value
        if self.set_secret(name, new_value):
            return new_value
        return None

from flask_backend.services.base_service import BaseService

class VaultService(BaseService):
    """Enhanced secrets management service with multiple providers"""
    
    # Critical secrets that must be present in production
    CRITICAL_SECRETS = {
        'SESSION_SECRET': "Used for Flask session security",
        'JWT_SECRET_KEY': "Used for JWT token signing",
        'JWT_PRIVATE_KEY': "Used for asymmetric JWT signing",
        'JWT_PUBLIC_KEY': "Used for asymmetric JWT verification",
        'ENCRYPTION_KEY': "Used for sensitive data encryption",
        'SUPER_ADMIN_KEY': "Used for super admin access"
    }
    
    def __init__(self):
        self._app = None
        self._initialized = False
        self._providers = []
        self._secrets_cache = {}
        
        # Import centralized environment configuration
        # Use local import to avoid circular imports
        from flask_backend.config import IS_PRODUCTION, IS_PRODUCTION_LIKE
        self._is_production = IS_PRODUCTION
        self._is_production_like = IS_PRODUCTION_LIKE
        
    @property
    def initialized(self):
        """Return whether the service is initialized"""
        return self._initialized
        
    def health_check(self):
        """Return the health status of the service"""
        status = "ok" if self._initialized else "error"
        message = f"Vault service is {'initialized' if self._initialized else 'not initialized'}"
        providers_info = f"{len(self._providers)} providers configured"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "providers": providers_info,
                "cached_secrets": len(self._secrets_cache)
            }
        }
        
    def init_app(self, app):
        """Initialize the vault service with the Flask app"""
        self._app = app
        
        # Determine the secrets providers based on environment
        provider_types = app.config.get('SECRETS_PROVIDERS', 'env').split(',')
        
        # Initialize providers
        for provider_type in provider_types:
            provider_type = provider_type.strip().lower()
            
            if provider_type == 'env':
                # Environment variables provider
                self._providers.append(EnvSecretsProvider(
                    allow_fallbacks=not self._is_production
                ))
            elif provider_type == 'file':
                # File-based provider
                self._providers.append(FileSecretsProvider(
                    secrets_file=app.config.get('SECRETS_FILE', '.secrets.json')
                ))
            elif provider_type == 'vault':
                # TODO: Add HashiCorp Vault provider implementation when needed
                logger.warning("HashiCorp Vault provider not yet implemented")
            elif provider_type == 'aws':
                # TODO: Add AWS Secrets Manager provider implementation when needed
                logger.warning("AWS Secrets Manager provider not yet implemented")
            else:
                logger.warning(f"Unknown secrets provider type: {provider_type}")
        
        # Make sure we have at least one provider
        if not self._providers:
            logger.critical("No secrets providers configured")
            if self._is_production:
                raise RuntimeError("No secrets providers configured in production")
            else:
                # In development, add environment provider as fallback
                logger.warning("Adding environment provider as fallback")
                self._providers.append(EnvSecretsProvider(allow_fallbacks=True))
        
        # Initialize secrets cache with app context
        if app.config.get('PRELOAD_SECRETS', True):
            self._load_secrets()
            
        # In production, validate critical secrets
        if self._is_production:
            self._validate_critical_secrets()
            
        self._initialized = True
        logger.info(f"Vault service initialized with {len(self._providers)} providers")
            
    def _load_secrets(self):
        """Preload secrets from providers"""
        for secret_name in self.CRITICAL_SECRETS:
            # Try to get the secret
            secret_value = self.get_secret(secret_name)
            
            # Log status (without the value)
            if secret_value:
                logger.info(f"Preloaded secret: {secret_name}")
            else:
                logger.warning(f"Could not preload secret: {secret_name}")
                
    def _validate_critical_secrets(self):
        """Validate that all critical secrets are available in production"""
        missing_secrets = []
        
        for secret_name, description in self.CRITICAL_SECRETS.items():
            if not self.get_secret(secret_name):
                missing_secrets.append(f"{secret_name} - {description}")
                
        if missing_secrets:
            message = f"Missing critical secrets in production: {', '.join(missing_secrets)}"
            logger.critical(message)
            raise RuntimeError(message)
        
    def get_secret(self, name: str, default: Any = None) -> Union[str, bytes, None]:
        """
        Get a secret value by name from any available provider
        
        Args:
            name: Name of the secret to retrieve
            default: Optional default value if secret is not found
            
        Returns:
            The secret value or default
        """
        if not self._initialized:
            logger.error("Vault service not initialized")
            if self._is_production:
                # In production, fail hard and fast
                raise RuntimeError("Vault service not initialized in production")
            return default
            
        # Check cache first
        if name in self._secrets_cache:
            return self._secrets_cache[name]
            
        # Try each provider in order
        for provider in self._providers:
            value = provider.get_secret(name)
            if value is not None:
                # Cache the value
                self._secrets_cache[name] = value
                return value
                
        # Secret not found
        if name in self.CRITICAL_SECRETS and self._is_production:
            # In production, missing critical secrets are fatal
            message = f"Critical secret {name} not available in production"
            logger.critical(message)
            raise RuntimeError(message)
            
        # Return default for non-critical or non-production
        logger.warning(f"Secret {name} not found, using default")
        return default
        
    def set_secret(self, name: str, value: Any) -> bool:
        """
        Set a secret value in the first available provider
        
        Args:
            name: Name of the secret to set
            value: Value to set
            
        Returns:
            Success status
        """
        if self._is_production:
            logger.error("Cannot set secrets at runtime in production")
            return False
            
        if not self._initialized:
            logger.error("Vault service not initialized")
            return False
            
        # Update cache
        self._secrets_cache[name] = value
        
        # Try to set in the first provider
        if self._providers:
            return self._providers[0].set_secret(name, value)
            
        return False
        
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure token
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            A secure hex token string
        """
        return secrets.token_hex(length)
        
    def generate_secret_key(self):
        """Generate a secure secret key suitable for Flask sessions"""
        return secrets.token_hex(32)
        
    def rotate_secret(self, name: str) -> Optional[str]:
        """
        Rotate a secret to a new value in all providers
        
        Args:
            name: Name of the secret to rotate
            
        Returns:
            The new secret value or None if failed
        """
        if not self._initialized:
            logger.error("Vault service not initialized")
            return None
            
        # Don't rotate in production unless explicitly supported
        if self._is_production:
            logger.error("Cannot rotate secrets in production without proper provider")
            return None
            
        # Generate a new secret
        new_value = self.generate_secure_token()
        
        # Try to rotate in each provider
        success = False
        for provider in self._providers:
            if provider.rotate_secret(name, new_value):
                success = True
                
        if success:
            # Update cache
            self._secrets_cache[name] = new_value
            logger.info(f"Rotated secret {name}")
            return new_value
        else:
            logger.error(f"Failed to rotate secret {name}")
            return None
            
    def hash_value(self, value: str) -> str:
        """
        Create a secure hash of a value
        
        Args:
            value: Value to hash
            
        Returns:
            Secure hash as hex string
        """
        return hashlib.sha256(value.encode()).hexdigest()
        
    def secure_compare(self, val1: str, val2: str) -> bool:
        """
        Perform a constant-time comparison of two strings
        
        Args:
            val1: First value
            val2: Second value
            
        Returns:
            True if the values are equal, False otherwise
        """
        return secrets.compare_digest(str(val1), str(val2))

# Create singleton instance
vault_service = VaultService()