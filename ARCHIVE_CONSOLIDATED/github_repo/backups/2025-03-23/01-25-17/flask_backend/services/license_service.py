import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from flask_backend.app import db
from flask_backend.models import LicenseKey, LicenseVerification, WhmcsInstance

logger = logging.getLogger(__name__)

class LicenseService:
    """Service for managing and verifying license keys"""
    
    def __init__(self):
        self.license_verification_interval = 86400  # 24 hours in seconds
    
    def verify_license(self, license_key, domain, ip_address=None, system_info=None):
        """
        Verify a license key for a specific domain
        
        Args:
            license_key: The license key to verify
            domain: The domain of the WHMCS instance
            ip_address: The IP address of the request
            system_info: Additional system information
            
        Returns:
            Dictionary with verification result
        """
        # Normalize domain (remove protocol and trailing slash)
        domain = self._normalize_domain(domain)
        
        # Find the license key in the database
        license_record = LicenseKey.query.filter_by(key=license_key).first()
        
        # Prepare verification result
        result = {
            'valid': False,
            'message': 'Invalid license key',
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if license exists
        if not license_record:
            logger.warning(f"License verification failed: License key not found - {license_key}")
            self._log_verification(license_key, domain, ip_address, False, "License key not found")
            return result
        
        # Check if license is active
        if license_record.status != 'active':
            message = f"License key is {license_record.status}"
            logger.warning(f"License verification failed: {message} - {license_key}")
            self._log_verification(license_key, domain, ip_address, False, message)
            result['message'] = message
            return result
        
        # Check if license has expired
        if license_record.expires_at and license_record.expires_at < datetime.now():
            message = "License key has expired"
            logger.warning(f"License verification failed: {message} - {license_key}")
            self._log_verification(license_key, domain, ip_address, False, message)
            result['message'] = message
            return result
        
        # Check if domain is allowed
        allowed_domains = []
        if license_record.allowed_domains:
            try:
                allowed_domains = json.loads(license_record.allowed_domains)
            except json.JSONDecodeError:
                # If JSON is invalid, treat as empty list
                allowed_domains = []
        
        # If allowed_domains is specified and non-empty, check if domain is in the list
        if allowed_domains and domain not in allowed_domains:
            message = f"Domain {domain} is not authorized for this license key"
            logger.warning(f"License verification failed: {message} - {license_key}")
            self._log_verification(license_key, domain, ip_address, False, message)
            result['message'] = message
            return result
        
        # Find or create WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            # Create new WHMCS instance entry
            whmcs_instance = WhmcsInstance(
                license_key=license_key,
                domain=domain
            )
            db.session.add(whmcs_instance)
        else:
            # Update last seen timestamp
            whmcs_instance.last_seen = datetime.now()
        
        db.session.commit()
        
        # License is valid
        result['valid'] = True
        result['message'] = 'License key verified successfully'
        
        # Log the successful verification
        self._log_verification(license_key, domain, ip_address, True, "License key verified successfully")
        
        logger.info(f"License verification successful for {domain} with key {license_key}")
        
        return result
    
    def get_license_info(self, license_key, domain):
        """
        Get detailed information about a license key
        
        Args:
            license_key: The license key
            domain: The domain of the WHMCS instance
            
        Returns:
            Dictionary with license information
        """
        # Normalize domain
        domain = self._normalize_domain(domain)
        
        # Find the license key in the database
        license_record = LicenseKey.query.filter_by(key=license_key).first()
        
        # Return limited info if license not found
        if not license_record:
            logger.warning(f"License info request failed: License key not found - {license_key}")
            return {
                'status': 'invalid',
                'message': 'License key not found',
                'expires': 'N/A',
                'registered_to': 'N/A',
                'features': {}
            }
        
        # Return basic info if license is not active
        if license_record.status != 'active':
            return {
                'status': license_record.status,
                'message': f'License key is {license_record.status}',
                'expires': license_record.expires_at.strftime('%Y-%m-%d') if license_record.expires_at else 'N/A',
                'registered_to': license_record.owner_name or 'N/A',
                'features': {}
            }
        
        # Parse features JSON
        features = {}
        if license_record.features:
            try:
                features = json.loads(license_record.features)
            except json.JSONDecodeError:
                features = {}
        
        # Return full license info
        return {
            'status': 'valid',
            'message': 'License information retrieved successfully',
            'expires': license_record.expires_at.strftime('%Y-%m-%d') if license_record.expires_at else 'N/A',
            'registered_to': license_record.owner_name or 'N/A',
            'max_banks': license_record.max_banks,
            'max_transactions': license_record.max_transactions,
            'features': features
        }
    
    def _log_verification(self, license_key, domain, ip_address, success, message):
        """
        Log a license verification attempt
        
        Args:
            license_key: The license key
            domain: The domain
            ip_address: The IP address of the request
            success: Whether the verification was successful
            message: The verification message
            
        Returns:
            None
        """
        verification_log = LicenseVerification(
            license_key=license_key,
            domain=domain,
            ip_address=ip_address,
            success=success,
            message=message
        )
        
        db.session.add(verification_log)
        db.session.commit()
    
    def _normalize_domain(self, domain):
        """
        Normalize a domain by removing protocol and trailing slash
        
        Args:
            domain: The domain to normalize
            
        Returns:
            Normalized domain string
        """
        # Remove protocol
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        
        # Remove trailing slash
        if domain.endswith('/'):
            domain = domain[:-1]
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain.lower()
    
    def create_license_key(self, owner_name, owner_email, max_banks=5, max_transactions=1000, 
                           expires_at=None, allowed_domains=None, features=None):
        """
        Create a new license key
        
        Args:
            owner_name: Name of the license owner
            owner_email: Email of the license owner
            max_banks: Maximum number of bank connections allowed
            max_transactions: Maximum number of transactions allowed
            expires_at: Expiration date (datetime object)
            allowed_domains: List of allowed domains
            features: Dictionary of features enabled for this license
            
        Returns:
            The created license key
        """
        # Generate a unique license key
        license_key = self._generate_license_key(owner_email)
        
        # Create license record
        license_record = LicenseKey(
            key=license_key,
            status='active',
            owner_name=owner_name,
            owner_email=owner_email,
            expires_at=expires_at,
            allowed_domains=json.dumps(allowed_domains) if allowed_domains else None,
            max_banks=max_banks,
            max_transactions=max_transactions,
            features=json.dumps(features) if features else None
        )
        
        db.session.add(license_record)
        db.session.commit()
        
        logger.info(f"Created new license key {license_key} for {owner_email}")
        
        return license_key
    
    def _generate_license_key(self, owner_email):
        """
        Generate a unique license key
        
        Args:
            owner_email: Email to use as seed for the license key
            
        Returns:
            A unique license key string
        """
        # Generate a seed based on email and timestamp
        seed = f"{owner_email}:{datetime.now().isoformat()}:{os.urandom(8).hex()}"
        
        # Create SHA-256 hash
        hash_obj = hashlib.sha256(seed.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Format as XXXX-XXXX-XXXX-XXXX
        license_key = f"{hash_hex[:4]}-{hash_hex[4:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}".upper()
        
        return license_key
