"""
Encryption Service

This module provides encryption and decryption functions for sensitive data.
It implements field-level encryption for secure credential storage and management.
"""
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, app=None):
        """Initialize the encryption service"""
        self.fernet = None
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        # Get encryption key from environment variable or generate one
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        if not encryption_key:
            logger.warning("No encryption key found in environment. Using app secret for key derivation.")
            # Derive a key from the app secret key
            encryption_key = self._derive_key_from_secret(app.secret_key)
        
        # Generate Fernet cipher for symmetric encryption
        try:
            self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
            self.initialized = True
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            self.initialized = False
    
    def _derive_key_from_secret(self, secret_key):
        """Derive a Fernet key from the application secret key"""
        # Use PBKDF2 to derive a key from the secret
        salt = b'payymo-encryption-salt'  # Fixed salt for reproducibility
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode() if isinstance(secret_key, str) else secret_key))
        return key
    
    def encrypt(self, data):
        """
        Encrypt sensitive data
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as a string
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return None
        
        if data is None:
            return None
        
        try:
            # Convert to bytes if string
            if isinstance(data, str):
                data = data.encode()
            
            # Encrypt the data
            encrypted_data = self.fernet.encrypt(data)
            
            # Return as string
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return None
    
    def decrypt(self, encrypted_data):
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Encrypted data as a string
            
        Returns:
            Decrypted data as a string
        """
        if not self.initialized:
            logger.error("Encryption service not initialized")
            return None
        
        if encrypted_data is None:
            return None
        
        try:
            # Convert to bytes if string
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            
            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Return as string
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return None

# Create singleton instance
encryption_service = EncryptionService()