"""
Encryption Service

This module provides field-level encryption for sensitive data in the database.
"""
import os
import base64
import logging
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Logger
logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, app=None):
        """
        Initialize the encryption service
        
        Args:
            app: Flask application instance
        """
        self.fernet = None
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the encryption service with a Flask app
        
        Args:
            app: Flask application instance
        """
        # Get encryption key from secrets service
        from flask_backend.services.secrets_service import secrets_service
        
        encryption_key = secrets_service.get_secret('ENCRYPTION_KEY')
        is_production = os.environ.get('ENVIRONMENT') == 'production'
        
        if not encryption_key:
            if is_production:
                logger.critical("No encryption key available in production environment.")
                logger.error("For security reasons, encryption is disabled in production without a proper key.")
                return
            else:
                # In development, generate a temporary key
                logger.warning("No encryption key found. Generating temporary development key.")
                encryption_key = secrets_service.generate_secure_token(32)
                # Store the temporary key in secrets service for consistency
                secrets_service.set_secret('ENCRYPTION_KEY', encryption_key)
                # Convert to valid Fernet key
                encryption_key = self._to_fernet_key(encryption_key)
                self.fernet = Fernet(encryption_key.encode())
        else:
            # Use provided encryption key
            # Ensure it's base64 encoded and 32 bytes when decoded
            if not self._is_valid_key(encryption_key):
                # Convert to valid Fernet key if needed
                encryption_key = self._to_fernet_key(encryption_key)
            
            self.fernet = Fernet(encryption_key.encode())
        
        self.initialized = True
        logger.info("Encryption service initialized successfully")
    
    def _is_valid_key(self, key):
        """
        Check if key is a valid Fernet key
        
        Args:
            key: Key to check
            
        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Try to create a Fernet instance with the key
            Fernet(key.encode())
            return True
        except Exception:
            return False
    
    def _to_fernet_key(self, key):
        """
        Convert arbitrary string to valid Fernet key
        
        Args:
            key: String to convert
            
        Returns:
            Valid Fernet key
        """
        # Hash the key to get consistent length
        key_bytes = hashlib.sha256(key.encode()).digest()
        # Base64 encode to get valid Fernet key
        return base64.urlsafe_b64encode(key_bytes).decode()
    
    def encrypt(self, data):
        """
        Encrypt data
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as string
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return data
        
        if data is None:
            return None
        
        try:
            # Convert data to bytes
            if isinstance(data, str):
                data_bytes = data.encode()
            else:
                data_bytes = str(data).encode()
            
            # Encrypt data
            encrypted_bytes = self.fernet.encrypt(data_bytes)
            # Return as base64 string
            return base64.b64encode(encrypted_bytes).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return data
    
    def decrypt(self, encrypted_data):
        """
        Decrypt data
        
        Args:
            encrypted_data: Encrypted data as string
            
        Returns:
            Decrypted data as string
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return encrypted_data
        
        if encrypted_data is None:
            return None
        
        try:
            # Convert from base64 string to bytes
            encrypted_bytes = base64.b64decode(encrypted_data)
            # Decrypt data
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            # Return as string
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return encrypted_data
    
    def encrypt_dict_fields(self, data_dict, field_names):
        """
        Encrypt specified fields in a dictionary
        
        Args:
            data_dict: Dictionary containing data to encrypt
            field_names: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return data_dict
        
        if not data_dict or not field_names:
            return data_dict
        
        # Create copy of dict to avoid modifying original
        result = data_dict.copy()
        
        # Encrypt each field
        for field in field_names:
            if field in result and result[field] is not None:
                result[field] = self.encrypt(result[field])
        
        return result
    
    def decrypt_dict_fields(self, data_dict, field_names):
        """
        Decrypt specified fields in a dictionary
        
        Args:
            data_dict: Dictionary containing data to decrypt
            field_names: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return data_dict
        
        if not data_dict or not field_names:
            return data_dict
        
        # Create copy of dict to avoid modifying original
        result = data_dict.copy()
        
        # Decrypt each field
        for field in field_names:
            if field in result and result[field] is not None:
                result[field] = self.decrypt(result[field])
        
        return result
    
    def encrypt_model_fields(self, model, field_names):
        """
        Encrypt specified fields in a model instance
        
        Args:
            model: SQLAlchemy model instance
            field_names: List of field names to encrypt
            
        Returns:
            Model instance with encrypted fields
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return model
        
        if not model or not field_names:
            return model
        
        # Encrypt each field
        for field in field_names:
            if hasattr(model, field) and getattr(model, field) is not None:
                setattr(model, field, self.encrypt(getattr(model, field)))
        
        return model
    
    def decrypt_model_fields(self, model, field_names):
        """
        Decrypt specified fields in a model instance
        
        Args:
            model: SQLAlchemy model instance
            field_names: List of field names to decrypt
            
        Returns:
            Model instance with decrypted fields
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return model
        
        if not model or not field_names:
            return model
        
        # Decrypt each field
        for field in field_names:
            if hasattr(model, field) and getattr(model, field) is not None:
                setattr(model, field, self.decrypt(getattr(model, field)))
        
        return model
    
# Create singleton instance
encryption_service = EncryptionService()