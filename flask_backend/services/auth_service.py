"""
Authentication Service

This module provides authentication and authorization functions for the application.
"""
import os
import uuid
import json
import logging
import secrets
from datetime import datetime, timedelta
from flask import current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_backend.app import db
from flask_backend.models import LicenseKey, WhmcsInstance
from flask_backend.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        """Initialize the authentication service"""
        self.token_expiry = 3600  # 1 hour in seconds
    
    def verify_license(self, license_key, domain):
        """
        Verify if a license key is valid for a domain
        
        Args:
            license_key: The license key to verify
            domain: The domain requesting verification
            
        Returns:
            Dictionary with verification result
        """
        if not license_key or not domain:
            return {
                'valid': False,
                'error': 'Missing license key or domain'
            }
        
        # Find the license key in the database
        license_record = LicenseKey.query.filter_by(key=license_key).first()
        
        if not license_record:
            logger.warning(f"Invalid license key attempt: {license_key}")
            return {
                'valid': False,
                'error': 'Invalid license key'
            }
        
        # Check if license is active
        if license_record.status != 'active':
            logger.warning(f"Non-active license key used: {license_key}, status: {license_record.status}")
            return {
                'valid': False,
                'error': f'License key is {license_record.status}',
                'status': license_record.status
            }
        
        # Check if license has expired
        if license_record.expires_at and license_record.expires_at < datetime.utcnow():
            logger.warning(f"Expired license key used: {license_key}")
            
            # Update license status to expired
            license_record.status = 'expired'
            db.session.commit()
            
            return {
                'valid': False,
                'error': 'License key has expired',
                'status': 'expired'
            }
        
        # Check if domain is allowed
        allowed_domains = []
        if license_record.allowed_domains:
            try:
                allowed_domains = json.loads(license_record.allowed_domains)
            except Exception as e:
                logger.error(f"Error parsing allowed domains: {str(e)}")
        
        if allowed_domains and domain not in allowed_domains:
            logger.warning(f"Unauthorized domain for license: {domain}")
            return {
                'valid': False,
                'error': 'Domain not authorized for this license key'
            }
        
        # Update last verification timestamp
        license_record.last_verified = datetime.utcnow()
        db.session.commit()
        
        return {
            'valid': True,
            'status': license_record.status,
            'expires_at': license_record.expires_at.isoformat() if license_record.expires_at else None,
            'max_banks': license_record.max_banks,
            'max_transactions': license_record.max_transactions,
            'features': json.loads(license_record.features) if license_record.features else {}
        }
    
    def verify_webhook_signature(self, signature, domain):
        """
        Verify webhook signature for a domain
        
        Args:
            signature: The webhook signature from the request header
            domain: The domain associated with the webhook
            
        Returns:
            Boolean indicating if signature is valid
        """
        if not signature or not domain:
            return False
        
        # Find the WHMCS instance
        instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not instance or not instance.webhook_secret:
            return False
        
        # Simple signature matching
        # In a production environment, consider using HMAC for signature verification
        return secrets.compare_digest(signature, instance.webhook_secret)
    
    def generate_api_key(self):
        """
        Generate a new API key
        
        Returns:
            String API key
        """
        # Generate a random UUID-based API key
        return str(uuid.uuid4())
    
    def rotate_api_keys(self, instance_id):
        """
        Rotate API keys for an instance
        
        Args:
            instance_id: ID of the WHMCS instance
            
        Returns:
            Dictionary with new API credentials
        """
        instance = WhmcsInstance.query.get(instance_id)
        
        if not instance:
            return {
                'success': False,
                'error': 'Instance not found'
            }
        
        # Store old credentials in case rollback is needed
        old_identifier = instance.api_identifier
        old_secret = instance.api_secret
        
        try:
            # Generate new API credentials
            new_secret = self.generate_api_key()
            
            # Update instance with new credentials
            instance.api_secret = new_secret
            db.session.commit()
            
            return {
                'success': True,
                'new_api_identifier': instance.api_identifier,
                'new_api_secret': new_secret
            }
        except Exception as e:
            # Rollback on error
            logger.error(f"Error rotating API keys: {str(e)}")
            instance.api_identifier = old_identifier
            instance.api_secret = old_secret
            db.session.rollback()
            
            return {
                'success': False,
                'error': 'Failed to rotate API keys'
            }
    
    def create_csrf_token(self):
        """
        Create a CSRF token for form protection
        
        Returns:
            String CSRF token
        """
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
            session['csrf_token_expiry'] = (datetime.utcnow() + 
                                           timedelta(seconds=current_app.config.get('CSRF_EXPIRATION', 3600))
                                          ).timestamp()
        
        # Check if token has expired
        elif session.get('csrf_token_expiry', 0) < datetime.utcnow().timestamp():
            # Generate a new token
            session['csrf_token'] = secrets.token_hex(32)
            session['csrf_token_expiry'] = (datetime.utcnow() + 
                                           timedelta(seconds=current_app.config.get('CSRF_EXPIRATION', 3600))
                                          ).timestamp()
        
        return session['csrf_token']
    
    def verify_csrf_token(self, token):
        """
        Verify a CSRF token against the session
        
        Args:
            token: The CSRF token to verify
            
        Returns:
            Boolean indicating if token is valid
        """
        if not token or not session.get('csrf_token'):
            return False
        
        # Check if token has expired
        if session.get('csrf_token_expiry', 0) < datetime.utcnow().timestamp():
            return False
        
        # Verify token
        return secrets.compare_digest(token, session['csrf_token'])
    
    def generate_secure_password(self, length=16):
        """
        Generate a cryptographically secure random password
        
        Args:
            length: Length of the password to generate (default: 16)
            
        Returns:
            Secure random password
        """
        # Ensure minimum length
        if length < current_app.config.get('PASSWORD_MIN_LENGTH', 12):
            length = current_app.config.get('PASSWORD_MIN_LENGTH', 12)
            
        # Generate password
        import string
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))

# Create singleton instance
auth_service = AuthService()