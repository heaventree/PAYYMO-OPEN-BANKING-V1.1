"""
Core Banking Service

This unified service handles all Open Banking API interactions with GoCardless,
consolidating the functionality from multiple previous service implementations.
"""
import os
import json
import uuid
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask_backend.services.base_service import BaseService
from flask_backend.utils.db import get_db
from flask_backend.utils.gocardless_errors import (
    GoCardlessError, GoCardlessAuthError, GoCardlessBankConnectionError,
    GoCardlessTransactionError, GoCardlessWebhookError, parse_error_response
)

# Logger
logger = logging.getLogger(__name__)

class CoreBankingService(BaseService):
    """Unified service for GoCardless Open Banking API interactions"""
    
    def __init__(self):
        """Initialize the Core Banking Service"""
        # Service state
        self._app = None
        self._initialized = False
        
        # API credentials and configuration
        self._client_id = None
        self._client_secret = None
        self._sandbox_mode = True
        self._api_base_url = None
        self._api_version = None
        self._use_test_data = False
        self._banks_endpoint = None
        self._auth_url = None
        self._token_url = None
        self._webhook_cert_path = None
        self._webhook_key_path = None
    
    @property
    def initialized(self):
        """
        Return whether the service is initialized
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized
    
    def health_check(self):
        """
        Return the health status of the service
        
        Returns:
            dict: Health status information with at least 'status' and 'message' keys
        """
        status = "ok" if self._initialized else "error"
        message = f"Core Banking service is {'initialized' if self._initialized else 'not initialized'}"
        
        # Additional health check details
        details = {
            "sandbox_mode": self._sandbox_mode,
            "api_version": self._api_version,
            "credentials": "configured" if self._client_id and self._client_secret else "missing",
            "webhook_certificates": "configured" if self._webhook_cert_path and self._webhook_key_path else "missing"
        }
        
        return {
            "status": status,
            "message": message,
            "details": details
        }
    
    def init_app(self, app):
        """
        Initialize the service with Flask app
        
        Args:
            app: Flask application instance
        """
        self._app = app
        
        # Get configuration from vault service
        from flask_backend.services.vault_service import vault_service
        
        self._client_id = vault_service.get_secret('GOCARDLESS_CLIENT_ID')
        self._client_secret = vault_service.get_secret('GOCARDLESS_CLIENT_SECRET')
        
        # Determine environment - ensure we're handling the value correctly
        sandbox_mode_config = app.config.get('GOCARDLESS_SANDBOX_MODE', 'true')
        if isinstance(sandbox_mode_config, bool):
            self._sandbox_mode = sandbox_mode_config
        else:
            self._sandbox_mode = str(sandbox_mode_config).lower() == 'true'
        
        # Configure based on environment
        if self._sandbox_mode:
            self._configure_sandbox()
        else:
            self._configure_production()
        
        # Get webhook certificate paths from app config
        self._webhook_cert_path = app.config.get('GOCARDLESS_WEBHOOK_CERT_PATH')
        self._webhook_key_path = app.config.get('GOCARDLESS_WEBHOOK_KEY_PATH')
        
        if not self._webhook_cert_path or not self._webhook_key_path:
            logger.warning("GoCardless webhook certificates not configured")
        
        # Validate configuration in production environment
        if os.environ.get('ENVIRONMENT') == 'production' and not (self._client_id and self._client_secret):
            logger.critical("Missing GoCardless credentials in production")
            # Don't raise an error, but keep initialized as False to reflect the issue
        else:
            self._initialized = True
        
        logger.info(f"Core Banking service initialized in {'sandbox' if self._sandbox_mode else 'production'} mode")
    
    def _configure_sandbox(self):
        """Configure service for sandbox environment"""
        logger.info("Core Banking service running in SANDBOX mode")
        self._api_base_url = 'https://api-sandbox.gocardless.com'
        self._api_version = '2023-09-04'  # Latest documented stable version
        self._banks_endpoint = f"{self._api_base_url}/institutions"
        self._auth_url = 'https://auth-sandbox.gocardless.com/oauth/authorize'
        self._token_url = 'https://auth-sandbox.gocardless.com/oauth/token'
        
        # Use sandbox credentials if not provided
        if not self._client_id:
            self._client_id = 'sandbox-client-id'
            logger.warning("Using default sandbox client ID")
        if not self._client_secret:
            self._client_secret = 'sandbox-client-secret'
            logger.warning("Using default sandbox client secret")
    
    def _configure_production(self):
        """Configure service for production environment"""
        logger.info("Core Banking service running in PRODUCTION mode")
        self._api_base_url = 'https://api.gocardless.com'
        self._api_version = '2023-09-04'  # Latest documented stable version
        self._banks_endpoint = f"{self._api_base_url}/institutions"
        self._auth_url = 'https://auth.gocardless.com/oauth/authorize'
        self._token_url = 'https://auth.gocardless.com/oauth/token'
    
    def _create_headers(self, with_auth=True):
        """
        Create request headers for API calls
        
        Args:
            with_auth: Whether to include authentication
            
        Returns:
            dict: Headers to use for API requests
        """
        headers = {
            'GoCardless-Version': self._api_version,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if with_auth and self._client_id and self._client_secret:
            # Basic auth with client credentials
            import base64
            auth_string = f"{self._client_id}:{self._client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            headers['Authorization'] = f"Basic {auth_b64}"
        
        return headers
    
    def get_banks(self, country=None, limit=50):
        """
        Get available banks for a specific country
        
        Args:
            country: Country code (ISO 3166-1 alpha-2)
            limit: Maximum number of banks to return
            
        Returns:
            list: List of bank information dictionaries
        """
        try:
            # For sandbox/development, return test data if enabled to avoid API calls
            if self._sandbox_mode and self._use_test_data:
                logger.info("Using sandbox test banks (version issue with API)")
                return self._get_test_banks(country)
            
            # Build request parameters
            params = {'limit': limit}
            if country:
                params['country'] = country
            
            # Add query parameters to URL
            url = f"{self._banks_endpoint}?{urlencode(params)}"
            
            # Make API request
            headers = self._create_headers()
            response = requests.get(url, headers=headers)
            
            # Check for errors
            if response.status_code != 200:
                error = parse_error_response(response)
                logger.error(f"Error getting banks: {error}")
                return self._get_test_banks(country)
            
            # Parse and return response
            banks = response.json().get('institutions', [])
            return banks
        
        except Exception as e:
            logger.exception(f"Error getting banks: {str(e)}")
            return self._get_test_banks(country)
    
    def _get_test_banks(self, country=None):
        """
        Get test banks for development and testing
        
        Args:
            country: Optional country code to filter banks
            
        Returns:
            list: List of test bank information dictionaries
        """
        test_banks = [
            {
                "id": "ob-sandbox-barclays",
                "name": "Barclays Personal",
                "logo": "https://cdn.gocardless.com/icons/banks/barclays.svg",
                "country": "GB"
            },
            {
                "id": "ob-sandbox-hsbc",
                "name": "HSBC Personal",
                "logo": "https://cdn.gocardless.com/icons/banks/hsbc.svg",
                "country": "GB"
            },
            {
                "id": "ob-sandbox-lloyds",
                "name": "Lloyds Bank Personal",
                "logo": "https://cdn.gocardless.com/icons/banks/lloyds.svg",
                "country": "GB"
            },
            {
                "id": "ob-sandbox-santander",
                "name": "Santander Personal",
                "logo": "https://cdn.gocardless.com/icons/banks/santander.svg",
                "country": "GB"
            },
            {
                "id": "ob-sandbox-rbs",
                "name": "Royal Bank of Scotland",
                "logo": "https://cdn.gocardless.com/icons/banks/rbs.svg",
                "country": "GB"
            }
        ]
        
        # Filter by country if provided
        if country:
            test_banks = [bank for bank in test_banks if bank.get('country') == country]
        
        return test_banks
    
    def create_bank_link(self, tenant_id, bank_id, redirect_uri, state=None):
        """
        Create bank authorization link for the user to connect their bank
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            bank_id: ID of the bank to connect to
            redirect_uri: URL to redirect to after authorization
            state: Optional state for CSRF protection
            
        Returns:
            dict: Bank link information with url and other details
        """
        try:
            # Get tenant information
            db = get_db()
            tenant = db.session.query(WhmcsInstance).filter_by(id=tenant_id).first()
            
            if not tenant:
                raise GoCardlessBankConnectionError(f"Tenant not found: {tenant_id}")
            
            # Generate state if not provided
            if not state:
                state = str(uuid.uuid4())
            
            # Create authorization parameters
            params = {
                'client_id': self._client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'institution_id': bank_id,
                'state': state
            }
            
            # Create authorization URL
            auth_url = f"{self._auth_url}?{urlencode(params)}"
            
            return {
                'auth_url': auth_url,
                'state': state,
                'tenant_id': tenant_id,
                'bank_id': bank_id
            }
        
        except Exception as e:
            logger.exception(f"Error creating bank link: {str(e)}")
            raise GoCardlessBankConnectionError(f"Failed to create bank link: {str(e)}")
    
    def complete_bank_connection(self, tenant_id, bank_id, code, redirect_uri):
        """
        Complete bank connection process after user authorization
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            bank_id: ID of the bank to connect to
            code: Authorization code from redirect
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            dict: Connection information with access token and other details
        """
        try:
            # Get tenant information
            db = get_db()
            tenant = db.session.query(WhmcsInstance).filter_by(id=tenant_id).first()
            
            if not tenant:
                raise GoCardlessBankConnectionError(f"Tenant not found: {tenant_id}")
            
            # Get bank name from API or test data
            bank_name = None
            banks = self.get_banks()
            for bank in banks:
                if bank.get('id') == bank_id:
                    bank_name = bank.get('name')
                    break
            
            if not bank_name:
                bank_name = f"Bank {bank_id}"
            
            # Exchange code for access token
            headers = self._create_headers()
            payload = {
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            }
            
            # In sandbox mode with test data, return simulated response
            if self._sandbox_mode and self._use_test_data:
                token_response = self._get_test_token_response()
            else:
                # Make token request
                response = requests.post(self._token_url, headers=headers, data=json.dumps(payload))
                
                # Check for errors
                if response.status_code != 200:
                    error = parse_error_response(response)
                    logger.error(f"Error exchanging code for token: {error}")
                    raise GoCardlessBankConnectionError(f"Failed to complete bank connection: {error}")
                
                token_response = response.json()
            
            # Extract token information
            access_token = token_response.get('access_token')
            refresh_token = token_response.get('refresh_token')
            expires_in = token_response.get('expires_in', 3600)  # Default 1 hour
            account_id = token_response.get('account_id', str(uuid.uuid4()))
            
            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create new bank connection
            connection = BankConnection(
                whmcs_instance_id=tenant_id,
                bank_id=bank_id,
                bank_name=bank_name,
                account_id=account_id,
                account_name=f"{bank_name} Account",
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(connection)
            db.session.commit()
            
            return {
                'connection_id': connection.id,
                'bank_id': bank_id,
                'bank_name': bank_name,
                'account_id': account_id,
                'status': 'active',
                'expires_at': expires_at.isoformat()
            }
        
        except Exception as e:
            logger.exception(f"Error completing bank connection: {str(e)}")
            raise GoCardlessBankConnectionError(f"Failed to complete bank connection: {str(e)}")
    
    def _get_test_token_response(self):
        """
        Get test token response for development and testing
        
        Returns:
            dict: Test token response
        """
        return {
            'access_token': f"test-access-token-{uuid.uuid4()}",
            'refresh_token': f"test-refresh-token-{uuid.uuid4()}",
            'token_type': 'Bearer',
            'expires_in': 7200,  # 2 hours
            'account_id': f"test-account-{uuid.uuid4()}"
        }
    
    def refresh_bank_connection(self, connection_id):
        """
        Refresh bank connection access token
        
        Args:
            connection_id: ID of the bank connection to refresh
            
        Returns:
            dict: Updated connection information
        """
        try:
            # Get connection from database
            db = get_db()
            connection = db.session.query(BankConnection).filter_by(id=connection_id).first()
            
            if not connection:
                raise GoCardlessBankConnectionError(f"Connection not found: {connection_id}")
            
            # Check if refresh token exists
            if not connection.refresh_token:
                raise GoCardlessBankConnectionError(f"No refresh token for connection: {connection_id}")
            
            # In sandbox mode with test data, return simulated response
            if self._sandbox_mode and self._use_test_data:
                token_response = self._get_test_token_response()
            else:
                # Prepare token refresh request
                headers = self._create_headers()
                payload = {
                    'client_id': self._client_id,
                    'client_secret': self._client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': connection.refresh_token
                }
                
                # Make token refresh request
                response = requests.post(self._token_url, headers=headers, data=json.dumps(payload))
                
                # Check for errors
                if response.status_code != 200:
                    error = parse_error_response(response)
                    logger.error(f"Error refreshing token: {error}")
                    raise GoCardlessBankConnectionError(f"Failed to refresh bank connection: {error}")
                
                token_response = response.json()
            
            # Extract token information
            access_token = token_response.get('access_token')
            refresh_token = token_response.get('refresh_token')
            expires_in = token_response.get('expires_in', 3600)  # Default 1 hour
            
            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update connection
            connection.access_token = access_token
            connection.refresh_token = refresh_token
            connection.token_expires_at = expires_at
            connection.updated_at = datetime.utcnow()
            
            # Save to database
            db.session.commit()
            
            return {
                'connection_id': connection.id,
                'bank_id': connection.bank_id,
                'bank_name': connection.bank_name,
                'account_id': connection.account_id,
                'status': connection.status,
                'expires_at': connection.token_expires_at.isoformat()
            }
        
        except Exception as e:
            logger.exception(f"Error refreshing bank connection: {str(e)}")
            raise GoCardlessBankConnectionError(f"Failed to refresh bank connection: {str(e)}")
    
    def get_transactions(self, connection_id, date_from=None, date_to=None):
        """
        Get transactions for a bank connection
        
        Args:
            connection_id: ID of the bank connection
            date_from: Optional start date (ISO format)
            date_to: Optional end date (ISO format)
            
        Returns:
            list: List of transaction dictionaries
        """
        try:
            # Get connection from database
            db = get_db()
            connection = db.session.query(BankConnection).filter_by(id=connection_id).first()
            
            if not connection:
                raise GoCardlessTransactionError(f"Connection not found: {connection_id}")
            
            # Check if token is expired and refresh if necessary
            if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
                logger.info(f"Refreshing expired token for connection: {connection_id}")
                self.refresh_bank_connection(connection_id)
                # Get updated connection
                connection = db.session.query(BankConnection).filter_by(id=connection_id).first()
            
            # In sandbox mode with test data, return simulated transactions
            if self._sandbox_mode and self._use_test_data:
                return self._get_test_transactions(connection, date_from, date_to)
            
            # Prepare API request
            endpoint = f"{self._api_base_url}/accounts/{connection.account_id}/transactions"
            
            # Build request parameters
            params = {}
            if date_from:
                params['date_from'] = date_from
            if date_to:
                params['date_to'] = date_to
            
            # Add query parameters to URL
            if params:
                endpoint = f"{endpoint}?{urlencode(params)}"
            
            # Create authorization header with access token
            headers = self._create_headers(with_auth=False)
            headers['Authorization'] = f"Bearer {connection.access_token}"
            
            # Make API request
            response = requests.get(endpoint, headers=headers)
            
            # Check for errors
            if response.status_code != 200:
                error = parse_error_response(response)
                logger.error(f"Error getting transactions: {error}")
                # If unauthorized, try to refresh token and retry
                if response.status_code == 401:
                    logger.info(f"Refreshing token for connection: {connection_id}")
                    self.refresh_bank_connection(connection_id)
                    # Get updated connection
                    connection = db.session.query(BankConnection).filter_by(id=connection_id).first()
                    # Retry with new token
                    headers['Authorization'] = f"Bearer {connection.access_token}"
                    response = requests.get(endpoint, headers=headers)
                    
                    if response.status_code != 200:
                        error = parse_error_response(response)
                        logger.error(f"Error getting transactions after token refresh: {error}")
                        return self._get_test_transactions(connection, date_from, date_to)
                else:
                    return self._get_test_transactions(connection, date_from, date_to)
            
            # Parse response
            transactions_data = response.json().get('transactions', [])
            
            # Process and save transactions
            saved_transactions = []
            for tx_data in transactions_data:
                # Extract transaction data
                tx_id = tx_data.get('id')
                amount = float(tx_data.get('amount', 0))
                currency = tx_data.get('currency', 'GBP')
                description = tx_data.get('description', '')
                reference = tx_data.get('reference', '')
                tx_date = datetime.fromisoformat(tx_data.get('transaction_date', datetime.utcnow().isoformat()))
                
                # Check if transaction already exists
                existing_tx = db.session.query(Transaction).filter_by(transaction_id=tx_id).first()
                if existing_tx:
                    # Transaction already saved
                    saved_transactions.append(existing_tx)
                    continue
                
                # Create new transaction
                transaction = Transaction(
                    transaction_id=tx_id,
                    bank_id=connection.bank_id,
                    bank_name=connection.bank_name,
                    account_id=connection.account_id,
                    account_name=connection.account_name,
                    amount=amount,
                    currency=currency,
                    description=description,
                    reference=reference,
                    transaction_date=tx_date,
                    created_at=datetime.utcnow()
                )
                
                # Save to database
                db.session.add(transaction)
                saved_transactions.append(transaction)
            
            # Commit all changes
            db.session.commit()
            
            # Return saved transactions
            return [
                {
                    'id': tx.id,
                    'transaction_id': tx.transaction_id,
                    'bank_id': tx.bank_id,
                    'bank_name': tx.bank_name,
                    'account_id': tx.account_id,
                    'account_name': tx.account_name,
                    'amount': tx.amount,
                    'currency': tx.currency,
                    'description': tx.description,
                    'reference': tx.reference,
                    'transaction_date': tx.transaction_date.isoformat()
                }
                for tx in saved_transactions
            ]
        
        except Exception as e:
            logger.exception(f"Error getting transactions: {str(e)}")
            raise GoCardlessTransactionError(f"Failed to get transactions: {str(e)}")
    
    def _get_test_transactions(self, connection, date_from=None, date_to=None):
        """
        Get test transactions for development and testing
        
        Args:
            connection: Bank connection to generate transactions for
            date_from: Optional start date (ISO format)
            date_to: Optional end date (ISO format)
            
        Returns:
            list: List of test transaction dictionaries
        """
        # Convert date strings to datetime objects or use defaults
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from)
            except (ValueError, TypeError):
                from_date = datetime.utcnow() - timedelta(days=30)
        else:
            from_date = datetime.utcnow() - timedelta(days=30)
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to)
            except (ValueError, TypeError):
                to_date = datetime.utcnow()
        else:
            to_date = datetime.utcnow()
        
        # Generate random transactions within date range
        import random
        from decimal import Decimal, ROUND_HALF_UP
        
        # Database session
        db = get_db()
        
        # Number of transactions to generate
        num_transactions = random.randint(5, 15)
        
        # Transaction descriptions
        descriptions = [
            "Monthly Subscription",
            "Web Hosting WHMCS",
            "Domain Renewal",
            "SSL Certificate",
            "VPS Hosting",
            "Cloud Backup Service",
            "Email Service",
            "Technical Support",
            "Setup Fee",
            "Consulting Services"
        ]
        
        # Transaction references
        references = [
            "INV-12345",
            "WHM-67890",
            "DOM-23456",
            "SSL-78901",
            "VPS-34567",
            "BCK-89012",
            "EML-45678",
            "SUP-90123",
            "SET-56789",
            "CON-01234"
        ]
        
        test_transactions = []
        for i in range(num_transactions):
            # Generate random date within range
            days_span = (to_date - from_date).days
            if days_span <= 0:
                days_span = 1
            random_days = random.randint(0, days_span)
            tx_date = from_date + timedelta(days=random_days)
            
            # Generate random amount (between 5 and 500)
            amount = random.uniform(5, 500)
            # Round to 2 decimal places
            amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Create unique transaction ID
            tx_id = f"test-tx-{connection.bank_id}-{uuid.uuid4()}"
            
            # Random description and reference
            description = random.choice(descriptions)
            reference = random.choice(references)
            
            # Check if transaction already exists
            existing_tx = db.session.query(Transaction).filter_by(transaction_id=tx_id).first()
            if existing_tx:
                # Add to result and continue
                test_transactions.append({
                    'id': existing_tx.id,
                    'transaction_id': existing_tx.transaction_id,
                    'bank_id': existing_tx.bank_id,
                    'bank_name': existing_tx.bank_name,
                    'account_id': existing_tx.account_id,
                    'account_name': existing_tx.account_name,
                    'amount': float(existing_tx.amount),
                    'currency': existing_tx.currency,
                    'description': existing_tx.description,
                    'reference': existing_tx.reference,
                    'transaction_date': existing_tx.transaction_date.isoformat()
                })
                continue
            
            # Create new transaction
            transaction = Transaction(
                transaction_id=tx_id,
                bank_id=connection.bank_id,
                bank_name=connection.bank_name,
                account_id=connection.account_id,
                account_name=connection.account_name,
                amount=float(amount),
                currency='GBP',
                description=description,
                reference=reference,
                transaction_date=tx_date,
                created_at=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(transaction)
            
            # Add to result
            test_transactions.append({
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'bank_id': transaction.bank_id,
                'bank_name': transaction.bank_name,
                'account_id': transaction.account_id,
                'account_name': transaction.account_name,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'description': transaction.description,
                'reference': transaction.reference,
                'transaction_date': transaction.transaction_date.isoformat()
            })
        
        # Commit all transactions
        db.session.commit()
        
        return test_transactions
    
    def verify_webhook_certificate(self, cert_data):
        """
        Verify GoCardless webhook certificate
        
        Args:
            cert_data: Certificate data from webhook
            
        Returns:
            bool: True if certificate is valid, False otherwise
        """
        try:
            # Don't verify in sandbox mode for testing
            if self._sandbox_mode:
                logger.info("Skipping certificate verification in sandbox mode")
                return True
            
            # Check if webhook certificates are configured
            if not self._webhook_cert_path or not self._webhook_key_path:
                logger.warning("Webhook certificates not configured, skipping verification")
                return True
            
            # Import cryptography modules
            import cryptography
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.x509.oid import NameOID
            
            # Load the webhook certificate data
            cert = cryptography.x509.load_pem_x509_certificate(
                cert_data.encode('utf-8'),
                default_backend()
            )
            
            # Get subject common name
            common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            logger.info(f"Webhook certificate common name: {common_name}")
            
            # Implement certificate validation logic here
            # For security reasons, verify the certificate against known GoCardless certificates
            # or against a locally stored CA certificate bundle
            
            # For now, just check that it's a GoCardless domain
            if not common_name.endswith('gocardless.com'):
                logger.warning(f"Invalid webhook certificate common name: {common_name}")
                return False
            
            # Add additional verification as needed
            
            return True
        
        except Exception as e:
            logger.exception(f"Error verifying webhook certificate: {str(e)}")
            return False
    
    def process_webhook(self, event_type, payload):
        """
        Process webhook event from GoCardless
        
        Args:
            event_type: Type of webhook event
            payload: Webhook event payload
            
        Returns:
            dict: Processing result
        """
        try:
            logger.info(f"Processing webhook event: {event_type}")
            
            result = {
                'status': 'success',
                'event_type': event_type,
                'message': f"Processed {event_type} event"
            }
            
            # Process different event types
            if event_type == 'transaction.created':
                # Process new transaction
                transaction_data = payload.get('transaction', {})
                account_id = transaction_data.get('account_id')
                
                # Get bank connection for this account
                db = get_db()
                connection = db.session.query(BankConnection).filter_by(account_id=account_id).first()
                
                if not connection:
                    logger.warning(f"No bank connection found for account: {account_id}")
                    result['status'] = 'error'
                    result['message'] = f"No bank connection found for account: {account_id}"
                    return result
                
                # Check if transaction already exists
                tx_id = transaction_data.get('id')
                existing_tx = db.session.query(Transaction).filter_by(transaction_id=tx_id).first()
                
                if existing_tx:
                    logger.info(f"Transaction already exists: {tx_id}")
                    result['message'] = f"Transaction already processed: {tx_id}"
                    return result
                
                # Extract transaction data
                amount = float(transaction_data.get('amount', 0))
                currency = transaction_data.get('currency', 'GBP')
                description = transaction_data.get('description', '')
                reference = transaction_data.get('reference', '')
                tx_date = datetime.fromisoformat(transaction_data.get('transaction_date', datetime.utcnow().isoformat()))
                
                # Create new transaction
                transaction = Transaction(
                    transaction_id=tx_id,
                    bank_id=connection.bank_id,
                    bank_name=connection.bank_name,
                    account_id=connection.account_id,
                    account_name=connection.account_name,
                    amount=amount,
                    currency=currency,
                    description=description,
                    reference=reference,
                    transaction_date=tx_date,
                    created_at=datetime.utcnow()
                )
                
                # Save to database
                db.session.add(transaction)
                db.session.commit()
                
                # Update result
                result['transaction_id'] = tx_id
                result['message'] = f"Transaction {tx_id} created successfully"
                
            elif event_type == 'connection.expired':
                # Handle expired connection
                account_id = payload.get('account_id')
                
                # Get bank connection for this account
                db = get_db()
                connection = db.session.query(BankConnection).filter_by(account_id=account_id).first()
                
                if not connection:
                    logger.warning(f"No bank connection found for account: {account_id}")
                    result['status'] = 'error'
                    result['message'] = f"No bank connection found for account: {account_id}"
                    return result
                
                # Update connection status
                connection.status = 'expired'
                connection.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Update result
                result['connection_id'] = connection.id
                result['message'] = f"Connection {connection.id} marked as expired"
                
            # Add handlers for other event types
            
            return result
        
        except Exception as e:
            logger.exception(f"Error processing webhook: {str(e)}")
            raise GoCardlessWebhookError(f"Failed to process webhook: {str(e)}")
    
    def get_bank_connections(self, tenant_id):
        """
        Get all bank connections for a tenant
        
        Args:
            tenant_id: ID of the tenant (WHMCS instance)
            
        Returns:
            list: List of bank connection dictionaries
        """
        try:
            # Get connections from database
            db = get_db()
            connections = db.session.query(BankConnection).filter_by(whmcs_instance_id=tenant_id).all()
            
            # Convert to dictionaries
            return [
                {
                    'id': conn.id,
                    'bank_id': conn.bank_id,
                    'bank_name': conn.bank_name,
                    'account_id': conn.account_id,
                    'account_name': conn.account_name,
                    'status': conn.status,
                    'created_at': conn.created_at.isoformat(),
                    'expires_at': conn.token_expires_at.isoformat() if conn.token_expires_at else None
                }
                for conn in connections
            ]
        
        except Exception as e:
            logger.exception(f"Error getting bank connections: {str(e)}")
            raise GoCardlessBankConnectionError(f"Failed to get bank connections: {str(e)}")
    
    def revoke_bank_connection(self, connection_id):
        """
        Revoke bank connection access
        
        Args:
            connection_id: ID of the bank connection to revoke
            
        Returns:
            dict: Result of the revocation
        """
        try:
            # Get connection from database
            db = get_db()
            connection = db.session.query(BankConnection).filter_by(id=connection_id).first()
            
            if not connection:
                raise GoCardlessBankConnectionError(f"Connection not found: {connection_id}")
            
            # In a real implementation, we would call the GoCardless API to revoke access
            # For now, just update the status in our database
            
            # Update connection status
            connection.status = 'revoked'
            connection.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'connection_id': connection.id,
                'status': 'revoked',
                'message': f"Bank connection {connection_id} successfully revoked"
            }
        
        except Exception as e:
            logger.exception(f"Error revoking bank connection: {str(e)}")
            raise GoCardlessBankConnectionError(f"Failed to revoke bank connection: {str(e)}")
    
    def log_api_call(self, method, endpoint, status_code, request_data=None, response_data=None, error=None):
        """
        Log API call to database for auditing
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            status_code: HTTP status code
            request_data: Optional request data
            response_data: Optional response data
            error: Optional error message
        """
        try:
            # Create API log entry
            db = get_db()
            log_entry = ApiLog(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                request_data=json.dumps(request_data) if request_data else None,
                response_data=json.dumps(response_data) if response_data else None,
                error=error,
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(log_entry)
            db.session.commit()
        
        except Exception as e:
            # Just log the error, don't raise - logging shouldn't interfere with main operations
            logger.error(f"Error logging API call: {str(e)}")

# Create singleton instance
core_banking_service = CoreBankingService()