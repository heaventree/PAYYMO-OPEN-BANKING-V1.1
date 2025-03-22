"""
WHMCS Testing Service
Provides functionality for integrating with external WHMCS instances for testing
Handles communication, error reporting, and debugging APIs
"""
import os
import json
import time
import logging
import requests
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import current_app
from flask_backend.app import db
from flask_backend.models import WhmcsInstance, ApiLog, LicenseKey

logger = logging.getLogger(__name__)

class WhmcsTestService:
    """Service for testing integration with WHMCS instances"""
    
    def __init__(self):
        """Initialize the service"""
        # Set up logging
        self.logger = logger
    
    def register_test_instance(self, domain, api_identifier, api_secret, admin_user=None, license_key=None):
        """
        Register a WHMCS instance for testing
        
        Args:
            domain: WHMCS instance domain
            api_identifier: WHMCS API identifier
            api_secret: WHMCS API secret
            admin_user: Admin username (optional)
            license_key: License key (optional)
            
        Returns:
            Dictionary with registration result and webhook_secret
        """
        try:
            # Check if domain already exists
            existing = WhmcsInstance.query.filter_by(domain=domain).first()
            if existing:
                # Update the existing record
                existing.api_identifier = api_identifier
                existing.api_secret = api_secret
                if admin_user:
                    existing.admin_user = admin_user
                if license_key:
                    existing.license_key = license_key
                existing.last_seen = datetime.utcnow()
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": "WHMCS instance updated successfully",
                    "webhook_secret": existing.webhook_secret,
                    "instance_id": existing.id
                }
            
            # Generate webhook secret
            webhook_secret = self._generate_webhook_secret(domain)
            
            # Create new instance
            instance = WhmcsInstance(
                domain=domain,
                api_identifier=api_identifier,
                api_secret=api_secret,
                admin_user=admin_user,
                license_key=license_key,
                webhook_secret=webhook_secret
            )
            
            db.session.add(instance)
            db.session.commit()
            
            return {
                "success": True,
                "message": "WHMCS instance registered successfully",
                "webhook_secret": webhook_secret,
                "instance_id": instance.id
            }
            
        except Exception as e:
            self.logger.error(f"Error registering WHMCS instance: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Error registering WHMCS instance: {str(e)}"
            }
    
    def verify_connection(self, domain, api_identifier, api_secret):
        """
        Verify connection to WHMCS instance
        
        Args:
            domain: WHMCS instance domain
            api_identifier: WHMCS API identifier
            api_secret: WHMCS API secret
            
        Returns:
            Dictionary with verification result and details
        """
        try:
            # Call the WHMCS API to verify connection
            api_url = f"https://{domain}/includes/api.php"
            
            # Prepare API parameters
            params = {
                'identifier': api_identifier,
                'secret': api_secret,
                'action': 'GetSystemInfo',
                'responsetype': 'json',
            }
            
            # Make request with timeout
            start_time = time.time()
            response = requests.post(api_url, data=params, timeout=10)
            end_time = time.time()
            
            # Log the API request
            self._log_api_interaction(
                endpoint=api_url,
                method="POST",
                request_data=json.dumps(params),
                response_data=response.text,
                status_code=response.status_code,
                duration_ms=int((end_time - start_time) * 1000)
            )
            
            # Check if request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('result') == 'success':
                        # Update the instance's last_seen timestamp
                        instance = WhmcsInstance.query.filter_by(domain=domain).first()
                        if instance:
                            instance.last_seen = datetime.utcnow()
                            db.session.commit()
                        
                        return {
                            "success": True,
                            "message": "Connection to WHMCS instance verified successfully",
                            "system_info": data.get('systeminfo', {})
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"WHMCS API error: {data.get('message', 'Unknown error')}",
                            "response": data
                        }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "message": "Invalid JSON response from WHMCS API",
                        "response": response.text
                    }
            else:
                return {
                    "success": False,
                    "message": f"HTTP error {response.status_code} from WHMCS API",
                    "response": response.text
                }
                
        except requests.exceptions.Timeout:
            # Log timeout error
            self._log_api_interaction(
                endpoint=f"https://{domain}/includes/api.php",
                method="POST",
                request_data=json.dumps(params),
                response_data="Request timed out",
                status_code=408,
                duration_ms=10000,
                error="Request timed out"
            )
            
            return {
                "success": False,
                "message": "Connection to WHMCS instance timed out"
            }
        except requests.exceptions.ConnectionError:
            # Log connection error
            self._log_api_interaction(
                endpoint=f"https://{domain}/includes/api.php",
                method="POST",
                request_data=json.dumps(params),
                response_data="Connection error",
                status_code=503,
                duration_ms=0,
                error="Connection error"
            )
            
            return {
                "success": False,
                "message": "Could not connect to WHMCS instance"
            }
        except Exception as e:
            self.logger.error(f"Error verifying WHMCS connection: {str(e)}")
            
            # Log general error
            self._log_api_interaction(
                endpoint=f"https://{domain}/includes/api.php",
                method="POST",
                request_data=json.dumps(params) if 'params' in locals() else "",
                response_data="",
                status_code=500,
                duration_ms=0,
                error=str(e)
            )
            
            return {
                "success": False,
                "message": f"Error verifying WHMCS connection: {str(e)}"
            }

    def test_webhook(self, domain):
        """
        Test webhook functionality by sending a test event
        
        Args:
            domain: WHMCS instance domain
            
        Returns:
            Dictionary with test result
        """
        try:
            # Get the instance
            instance = WhmcsInstance.query.filter_by(domain=domain).first()
            if not instance:
                return {
                    "success": False,
                    "message": "WHMCS instance not found"
                }
            
            # Build webhook URL
            webhook_url = f"https://{domain}/modules/addons/payymo/webhook.php"
            
            # Prepare test payload
            payload = {
                "event": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "message": "This is a test webhook event"
                }
            }
            
            # Calculate signature
            signature = self._calculate_webhook_signature(payload, instance.webhook_secret)
            
            # Make request with timeout
            headers = {
                "X-Payymo-Signature": signature,
                "Content-Type": "application/json"
            }
            
            start_time = time.time()
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            end_time = time.time()
            
            # Log the API request
            self._log_api_interaction(
                endpoint=webhook_url,
                method="POST",
                request_data=json.dumps(payload),
                response_data=response.text,
                status_code=response.status_code,
                duration_ms=int((end_time - start_time) * 1000)
            )
            
            # Check if request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "success": True,
                        "message": "Webhook test sent successfully",
                        "response": data
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "message": "Webhook test sent, but response was not JSON",
                        "response": response.text
                    }
            else:
                return {
                    "success": False,
                    "message": f"HTTP error {response.status_code} from webhook",
                    "response": response.text
                }
                
        except requests.exceptions.Timeout:
            # Log timeout error
            self._log_api_interaction(
                endpoint=f"https://{domain}/modules/addons/payymo/webhook.php",
                method="POST",
                request_data=json.dumps(payload) if 'payload' in locals() else "",
                response_data="Request timed out",
                status_code=408,
                duration_ms=10000,
                error="Request timed out"
            )
            
            return {
                "success": False,
                "message": "Webhook test timed out"
            }
        except requests.exceptions.ConnectionError:
            # Log connection error
            self._log_api_interaction(
                endpoint=f"https://{domain}/modules/addons/payymo/webhook.php",
                method="POST",
                request_data=json.dumps(payload) if 'payload' in locals() else "",
                response_data="Connection error",
                status_code=503,
                duration_ms=0,
                error="Connection error"
            )
            
            return {
                "success": False,
                "message": "Could not connect to WHMCS webhook URL"
            }
        except Exception as e:
            self.logger.error(f"Error testing webhook: {str(e)}")
            
            # Log general error
            self._log_api_interaction(
                endpoint=f"https://{domain}/modules/addons/payymo/webhook.php",
                method="POST",
                request_data=json.dumps(payload) if 'payload' in locals() else "",
                response_data="",
                status_code=500,
                duration_ms=0,
                error=str(e)
            )
            
            return {
                "success": False,
                "message": f"Error testing webhook: {str(e)}"
            }
    
    def log_error(self, domain, error_type, error_message, error_context=None):
        """
        Log an error from a WHMCS instance
        
        Args:
            domain: WHMCS instance domain
            error_type: Type of error (e.g., "api", "webhook", "module")
            error_message: Error message
            error_context: Additional context for the error (optional)
            
        Returns:
            Dictionary with logging result
        """
        try:
            # Get the instance
            instance = WhmcsInstance.query.filter_by(domain=domain).first()
            if not instance:
                return {
                    "success": False,
                    "message": "WHMCS instance not found"
                }
            
            # Create error log
            log_entry = ApiLog(
                endpoint=f"{domain}/error/{error_type}",
                method="ERROR",
                request_data=json.dumps(error_context) if error_context else "",
                response_data="",
                status_code=500,
                ip_address="",
                user_agent="WHMCS Module",
                duration_ms=0,
                error=error_message
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            # Log to app logger as well
            self.logger.error(f"WHMCS Error ({domain}/{error_type}): {error_message}")
            
            return {
                "success": True,
                "message": "Error logged successfully",
                "log_id": log_entry.id
            }
            
        except Exception as e:
            self.logger.error(f"Error logging WHMCS error: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Error logging WHMCS error: {str(e)}"
            }
    
    def get_status(self, domain):
        """
        Get status information for a WHMCS instance
        
        Args:
            domain: WHMCS instance domain
            
        Returns:
            Dictionary with status information
        """
        try:
            # Get the instance
            instance = WhmcsInstance.query.filter_by(domain=domain).first()
            if not instance:
                return {
                    "success": False,
                    "message": "WHMCS instance not found"
                }
            
            # Get license key if available
            license_info = None
            if instance.license_key:
                license_key = LicenseKey.query.filter_by(key=instance.license_key).first()
                if license_key:
                    license_info = {
                        "status": license_key.status,
                        "expires_at": license_key.expires_at.isoformat() if license_key.expires_at else None,
                        "max_banks": license_key.max_banks,
                        "max_transactions": license_key.max_transactions
                    }
            
            # Get bank connections
            bank_connections = [{
                "id": conn.id,
                "bank_name": conn.bank_name,
                "account_name": conn.account_name,
                "status": conn.status,
                "token_expires_at": conn.token_expires_at.isoformat() if conn.token_expires_at else None
            } for conn in instance.bank_connections]
            
            # Get Stripe connections
            stripe_connections = [{
                "id": conn.id,
                "account_name": conn.account_name,
                "account_email": conn.account_email,
                "status": conn.status,
                "account_type": conn.account_type,
                "account_country": conn.account_country,
                "token_expires_at": conn.token_expires_at.isoformat() if conn.token_expires_at else None
            } for conn in instance.stripe_connections]
            
            # Get recent errors
            recent_errors = ApiLog.query.filter(
                ApiLog.endpoint.like(f"{domain}/%"),
                ApiLog.method == "ERROR"
            ).order_by(ApiLog.created_at.desc()).limit(5).all()
            
            error_logs = [{
                "id": log.id,
                "error_type": log.endpoint.split('/')[-1] if '/' in log.endpoint else "unknown",
                "error": log.error,
                "context": log.request_data,
                "created_at": log.created_at.isoformat()
            } for log in recent_errors]
            
            return {
                "success": True,
                "instance_id": instance.id,
                "domain": instance.domain,
                "last_seen": instance.last_seen.isoformat(),
                "license": license_info,
                "bank_connections": bank_connections,
                "stripe_connections": stripe_connections,
                "recent_errors": error_logs,
                "webhook_secret": instance.webhook_secret
            }
            
        except Exception as e:
            self.logger.error(f"Error getting WHMCS instance status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting WHMCS instance status: {str(e)}"
            }
            
    def _generate_webhook_secret(self, domain):
        """Generate a unique webhook secret for a domain"""
        timestamp = datetime.utcnow().timestamp()
        random_seed = f"{domain}_{timestamp}_{os.urandom(8).hex()}"
        return hashlib.sha256(random_seed.encode()).hexdigest()[:64]
    
    def _calculate_webhook_signature(self, payload, secret):
        """Calculate signature for webhook payload"""
        payload_str = json.dumps(payload, separators=(',', ':'))
        return hashlib.sha256(f"{payload_str}{secret}".encode()).hexdigest()
    
    def _log_api_interaction(self, endpoint, method, request_data, response_data, status_code, duration_ms, error=None):
        """Log an API interaction to the database"""
        try:
            # Mask sensitive data
            masked_request = self._mask_sensitive_data(request_data)
            masked_response = self._mask_sensitive_data(response_data)
            
            log_entry = ApiLog(
                endpoint=endpoint,
                method=method,
                request_data=masked_request,
                response_data=masked_response,
                status_code=status_code,
                ip_address="",
                user_agent="WhmcsTestService",
                duration_ms=duration_ms,
                error=error
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error logging API interaction: {str(e)}")
            db.session.rollback()
            return False
    
    def _mask_sensitive_data(self, data_str):
        """Mask sensitive data in request/response data"""
        if not data_str:
            return data_str
            
        try:
            # If it's a JSON string, parse it and mask sensitive fields
            data = json.loads(data_str)
            
            # Fields to mask
            sensitive_fields = ['secret', 'password', 'api_secret', 'token', 'access_token', 'refresh_token']
            
            # Recursively mask sensitive data
            def mask_dict(d):
                if not isinstance(d, dict):
                    return d
                    
                for key, value in d.items():
                    if isinstance(value, dict):
                        d[key] = mask_dict(value)
                    elif isinstance(value, list):
                        d[key] = [mask_dict(item) if isinstance(item, dict) else item for item in value]
                    elif isinstance(value, str) and any(sf in key.lower() for sf in sensitive_fields):
                        # Mask the value
                        if len(value) > 8:
                            d[key] = value[:4] + '*' * (len(value) - 8) + value[-4:]
                        else:
                            d[key] = '*' * len(value)
                            
                return d
                
            masked_data = mask_dict(data)
            return json.dumps(masked_data)
        except json.JSONDecodeError:
            # If it's not JSON, just return as is
            return data_str
        except Exception as e:
            self.logger.error(f"Error masking sensitive data: {str(e)}")
            return data_str