import os
import json
import uuid
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask_backend.app import db
from flask_backend.models import BankConnection, WhmcsInstance, Transaction, ApiLog
from flask_backend.utils.gocardless_errors import (
    GoCardlessError, GoCardlessAuthError, GoCardlessBankConnectionError,
    GoCardlessTransactionError, GoCardlessWebhookError, parse_error_response
)

logger = logging.getLogger(__name__)

class GoCardlessService:
    """Service for interacting with the GoCardless Open Banking API"""
    
    def __init__(self):
        # Get API credentials from environment
        self.client_id = os.environ.get('GOCARDLESS_CLIENT_ID')
        self.client_secret = os.environ.get('GOCARDLESS_CLIENT_SECRET')
        
        # Try to get sandbox mode from app config first
        try:
            from flask import current_app
            sandbox_setting = current_app.config.get('GOCARDLESS_SANDBOX_MODE', 'true')
            self.sandbox_mode = sandbox_setting.lower() == 'true'
            logger.info(f"Using GoCardless sandbox mode from app config: {self.sandbox_mode}")
        except Exception as e:
            # Fallback to environment variable if app context is not available
            self.sandbox_mode = os.environ.get('GOCARDLESS_SANDBOX_MODE', 'true').lower() == 'true'
            logger.info(f"Using GoCardless sandbox mode from environment: {self.sandbox_mode}")
        
        if self.sandbox_mode:
            logger.info("GoCardless service running in SANDBOX mode")
            self.api_base_url = 'https://api-sandbox.gocardless.com'
            # Use a supported API version for the GoCardless Open Banking API
            self.api_version = '2023-09-04'  # Updated to the latest documented stable version
            # Update endpoint to match GoCardless API structure 
            self.banks_endpoint = f"{self.api_base_url}/institutions"
            self.auth_url = 'https://auth-sandbox.gocardless.com/oauth/authorize'
            self.token_url = 'https://auth-sandbox.gocardless.com/oauth/token'
            
            # Use sandbox credentials if not provided
            if not self.client_id:
                self.client_id = 'sandbox-client-id'
                logger.info("Using default sandbox client ID")
            if not self.client_secret:
                self.client_secret = 'sandbox-client-secret'
                logger.info("Using default sandbox client secret")
        else:
            logger.info("GoCardless service running in PRODUCTION mode")
            self.api_base_url = 'https://api.gocardless.com'
            # Use a supported API version for the GoCardless Open Banking API
            self.api_version = '2023-09-04'  # Updated to the latest documented stable version
            # Update endpoint to match GoCardless API structure
            self.banks_endpoint = f"{self.api_base_url}/institutions"
            self.auth_url = 'https://auth.gocardless.com/oauth/authorize'
            self.token_url = 'https://auth.gocardless.com/oauth/token'
        
        # Get Flask app for configuration (if available)
        try:
            from flask import current_app
            # Certificate paths for webhook verification from app config
            self.webhook_cert_path = current_app.config.get('GOCARDLESS_WEBHOOK_CERT_PATH')
            self.webhook_key_path = current_app.config.get('GOCARDLESS_WEBHOOK_KEY_PATH')
            logger.info(f"Using certificate paths from app config: {self.webhook_cert_path}, {self.webhook_key_path}")
        except Exception as e:
            # Fallback to environment variables if Flask app context is not available
            logger.warning(f"Could not get paths from app config: {str(e)}")
            self.webhook_cert_path = os.environ.get('GOCARDLESS_WEBHOOK_CERT_PATH')
            self.webhook_key_path = os.environ.get('GOCARDLESS_WEBHOOK_KEY_PATH')
        
        # Dictionary to store state parameters for OAuth flow
        self.oauth_states = {}
    
    def check_health(self):
        """Check the health of the GoCardless API"""
        try:
            # Perform a simple API request to check connectivity
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'GoCardless-Version': self.api_version
            }
            
            response = requests.get(
                self.banks_endpoint,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("GoCardless API health check succeeded")
                return True
            else:
                logger.warning(f"GoCardless API health check failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"GoCardless health check failed: {str(e)}")
            return False
            
    def get_available_banks(self, country=None, limit=50):
        """
        Get a list of available banks from GoCardless
        
        Args:
            country: Two-letter country code to filter banks (e.g., 'GB')
            limit: Maximum number of banks to return
            
        Returns:
            List of bank dictionaries with id, name, logo, etc.
        """
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'GoCardless-Version': self.api_version
            }
            
            # Set up query parameters
            params = {'limit': limit}
            if country:
                params['country'] = country
                
            # In sandbox mode, return some mock banks if API call fails
            if self.sandbox_mode:
                try:
                    # Try to get real banks from sandbox API
                    response = requests.get(
                        self.banks_endpoint,
                        headers=headers,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        banks_data = response.json()
                        # Check for different response formats
                        if 'institutions' in banks_data:
                            banks = banks_data.get('institutions', [])
                        else:
                            # Direct list of institutions
                            banks = banks_data
                            
                        logger.info(f"Retrieved {len(banks)} banks from GoCardless sandbox API")
                        return banks
                    else:
                        logger.warning(f"Failed to get banks from sandbox API: Status {response.status_code}, Response: {response.text}")
                except Exception as e:
                    logger.warning(f"Failed to get banks from sandbox API: {str(e)}")
                    
                # If API call fails in sandbox mode, return some sandbox test banks
                logger.info("Using sandbox test banks")
                return [
                    {
                        'id': 'test-bank-001',
                        'name': 'Test Bank UK',
                        'logo': 'https://via.placeholder.com/150x150.png?text=Test+Bank',
                        'country': 'GB',
                        'available_payments': True
                    },
                    {
                        'id': 'test-bank-002',
                        'name': 'Sandbox Bank',
                        'logo': 'https://via.placeholder.com/150x150.png?text=Sandbox+Bank',
                        'country': 'GB',
                        'available_payments': True
                    },
                    {
                        'id': 'test-bank-003',
                        'name': 'Open Banking Test',
                        'logo': 'https://via.placeholder.com/150x150.png?text=Open+Banking',
                        'country': 'GB',
                        'available_payments': True
                    },
                    {
                        'id': 'test-bank-004',
                        'name': 'Dev Bank',
                        'logo': 'https://via.placeholder.com/150x150.png?text=Dev+Bank',
                        'country': 'GB',
                        'available_payments': True
                    },
                    {
                        'id': 'test-bank-005',
                        'name': 'Mock Banking Corp',
                        'logo': 'https://via.placeholder.com/150x150.png?text=Mock+Bank',
                        'country': 'GB',
                        'available_payments': True
                    }
                ]
            
            # Production mode - get real banks from API
            response = requests.get(
                self.banks_endpoint,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to get banks: Status {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                
                # Parse error and raise proper exception
                error = parse_error_response(response, "Failed to get available banks")
                raise GoCardlessBankConnectionError(
                    message=f"Could not retrieve banks: {error.message}",
                    error_type="bank_list_error",
                    http_status=response.status_code,
                    details={"country": country}
                )
            
            banks_data = response.json()
            # Check for different response formats
            if 'institutions' in banks_data:
                banks = banks_data.get('institutions', [])
            else:
                # Direct list of institutions
                banks = banks_data
            
            logger.info(f"Retrieved {len(banks)} banks from GoCardless API")
            return banks
            
        except GoCardlessError:
            # Re-raise GoCardless errors
            raise
        except Exception as e:
            logger.error(f"Error getting available banks: {str(e)}")
            raise GoCardlessBankConnectionError(
                message=f"Error getting available banks: {str(e)}",
                error_type="bank_list_error",
                http_status=500
            )
    
    def get_authorization_url(self, domain, redirect_uri):
        """
        Generate GoCardless authorization URL for OAuth flow
        
        Args:
            domain: WHMCS instance domain
            redirect_uri: Callback URL after authorization
            
        Returns:
            Authorization URL string
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Generate a unique state parameter to prevent CSRF
        state = str(uuid.uuid4())
        
        # Store the state with domain information
        self.oauth_states[state] = {
            'domain': domain,
            'redirect_uri': redirect_uri,
            'timestamp': datetime.now().isoformat()
        }
        
        # Build the authorization URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'bank_account_read transaction_read',
            'state': state
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        
        # Log the authorization initiation
        logger.info(f"Generated GoCardless authorization URL for {domain}")
        
        return auth_url
    
    def process_callback(self, code, state):
        """
        Process OAuth callback from GoCardless
        
        Args:
            code: Authorization code from callback
            state: State parameter from callback
            
        Returns:
            Dictionary with bank account information
        """
        # Verify state parameter to prevent CSRF
        if state not in self.oauth_states:
            raise ValueError("Invalid state parameter")
        
        # Get stored state data
        state_data = self.oauth_states.pop(state)
        domain = state_data['domain']
        redirect_uri = state_data['redirect_uri']
        
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Exchange authorization code for access token
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        token_response = requests.post(
            self.token_url,
            headers={'Content-Type': 'application/json'},
            json=token_data
        )
        
        if token_response.status_code != 200:
            logger.error(f"Failed to exchange code for token: {token_response.text}")
            # Parse error response and raise appropriate exception
            error = parse_error_response(token_response, "OAuth token exchange failed")
            raise error
        
        tokens = token_response.json()
        
        # Get bank account information
        account_info = self._get_bank_account_info(tokens['access_token'])
        
        # Store the bank connection
        bank_connection = BankConnection(
            whmcs_instance_id=whmcs_instance.id,
            bank_id=account_info['bank_id'],
            bank_name=account_info['bank_name'],
            account_id=account_info['account_id'],
            account_name=account_info['account_name'],
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_expires_at=datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600)),
            status='active'
        )
        
        db.session.add(bank_connection)
        db.session.commit()
        
        logger.info(f"Successfully connected bank account for {domain}: {account_info['bank_name']} - {account_info['account_name']}")
        
        return {
            'success': True,
            'account': account_info
        }
    
    def _get_bank_account_info(self, access_token):
        """
        Get bank account information using the access token
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dictionary with bank account details
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'GoCardless-Version': self.api_version
        }
        
        # Updated endpoint for accounts
        accounts_endpoint = f"{self.api_base_url}/accounts"
        
        response = requests.get(
            accounts_endpoint,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get bank account info: {response.text}")
            error = parse_error_response(response, "Failed to get bank account information")
            raise GoCardlessBankConnectionError(
                message=f"Could not retrieve account information: {error.message}",
                error_type="account_access_error",
                http_status=response.status_code,
                details={"response": response.text}
            )
        
        data = response.json()
        
        # Check for different response formats
        accounts = []
        if isinstance(data, list):
            # Direct list of accounts
            accounts = data
        elif 'accounts' in data:
            # Object with accounts property
            accounts = data.get('accounts', [])
        else:
            # Single account object
            accounts = [data]
            
        if not accounts or len(accounts) == 0:
            raise GoCardlessBankConnectionError(
                message="No bank accounts found",
                error_type="no_accounts",
                http_status=404
            )
        
        account = accounts[0]
        
        # Handle different property names in API response
        account_id = account.get('id', account.get('account_id'))
        institution_id = account.get('institution_id', account.get('bank_id'))
        institution_name = account.get('institution_name', account.get('bank_name'))
        
        if not account_id or not institution_id:
            raise GoCardlessBankConnectionError(
                message="Invalid account data returned from API",
                error_type="invalid_account_data",
                http_status=500,
                details={"account": account}
            )
        
        return {
            'account_id': account_id,
            'bank_id': institution_id,
            'bank_name': institution_name,
            'account_name': account.get('name', 'Account'),
            'currency': account.get('currency', 'GBP')
        }
    
    def fetch_transactions(self, domain, account_id, from_date=None, to_date=None):
        """
        Fetch transactions from GoCardless for a specific bank account
        
        Args:
            domain: WHMCS instance domain
            account_id: Bank account ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            List of transactions
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Find the bank connection
        bank_connection = BankConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not bank_connection:
            raise ValueError(f"Bank connection not found for account: {account_id}")
        
        # Check if token is expired and refresh if needed
        if bank_connection.token_expires_at and bank_connection.token_expires_at < datetime.now():
            if not bank_connection.refresh_token:
                bank_connection.status = 'expired'
                db.session.commit()
                raise ValueError("Access token expired and no refresh token available")
            
            self._refresh_token(bank_connection)
        
        # Set up date range parameters
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch transactions from GoCardless
        headers = {
            'Authorization': f'Bearer {bank_connection.access_token}',
            'Accept': 'application/json',
            'GoCardless-Version': self.api_version
        }
        
        params = {
            'from_date': from_date,
            'to_date': to_date
        }
        
        # Updated transactions endpoint
        transactions_endpoint = f"{self.api_base_url}/accounts/{account_id}/transactions"
        
        response = requests.get(
            transactions_endpoint,
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch transactions: {response.text}")
            error = parse_error_response(response, "Failed to fetch transactions")
            raise GoCardlessTransactionError(
                message=f"Could not retrieve transactions: {error.message}",
                error_type="transaction_fetch_error",
                error_response=error.error_response,
                http_status=response.status_code,
                details={"account_id": account_id, "date_range": f"{from_date} to {to_date}"}
            )
        
        # Get transactions data, handling different API response formats
        response_data = response.json()
        transactions_data = []
        
        # Check for different response formats
        if isinstance(response_data, list):
            # Direct list of transactions
            transactions_data = response_data
        elif 'transactions' in response_data:
            # Object with transactions property
            transactions_data = response_data.get('transactions', [])
        elif 'items' in response_data:
            # Object with items property (for paged results)
            transactions_data = response_data.get('items', [])
        
        # Store transactions in database and return the list
        stored_transactions = []
        
        for transaction_data in transactions_data:
            # Check if transaction already exists
            existing = Transaction.query.filter_by(transaction_id=transaction_data['id']).first()
            
            if existing:
                # Skip if already exists
                stored_transactions.append(existing)
                continue
            
            # Create new transaction record
            transaction = Transaction(
                transaction_id=transaction_data['id'],
                bank_id=bank_connection.bank_id,
                bank_name=bank_connection.bank_name,
                account_id=bank_connection.account_id,
                account_name=bank_connection.account_name,
                amount=float(transaction_data['amount']),
                currency=transaction_data.get('currency', 'GBP'),
                description=transaction_data.get('description', ''),
                reference=transaction_data.get('reference', ''),
                transaction_date=datetime.strptime(transaction_data['date'], '%Y-%m-%d')
            )
            
            db.session.add(transaction)
            stored_transactions.append(transaction)
        
        db.session.commit()
        
        logger.info(f"Retrieved {len(stored_transactions)} transactions for {domain} account {account_id}")
        
        # Convert to dictionary for JSON response
        return [
            {
                'id': t.id,
                'transaction_id': t.transaction_id,
                'bank_name': t.bank_name,
                'account_name': t.account_name,
                'amount': t.amount,
                'currency': t.currency,
                'description': t.description,
                'reference': t.reference,
                'transaction_date': t.transaction_date.strftime('%Y-%m-%d')
            }
            for t in stored_transactions
        ]
    
    def _refresh_token(self, bank_connection):
        """
        Refresh an expired OAuth token
        
        Args:
            bank_connection: BankConnection object with expired token
            
        Returns:
            None (updates the bank_connection object)
        """
        if not bank_connection.refresh_token:
            raise ValueError("No refresh token available")
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': bank_connection.refresh_token
        }
        
        token_response = requests.post(
            self.token_url,
            headers={'Content-Type': 'application/json'},
            json=token_data
        )
        
        if token_response.status_code != 200:
            logger.error(f"Failed to refresh token: {token_response.text}")
            # Update connection status
            bank_connection.status = 'expired'
            db.session.commit()
            
            # Parse error response and raise appropriate exception
            error = parse_error_response(token_response, "OAuth token refresh failed")
            raise GoCardlessAuthError(
                message=f"Could not refresh access token: {error.message}",
                error_response=error.error_response,
                http_status=token_response.status_code
            )
        
        tokens = token_response.json()
        
        # Update the bank connection with new tokens
        bank_connection.access_token = tokens['access_token']
        bank_connection.refresh_token = tokens.get('refresh_token', bank_connection.refresh_token)
        bank_connection.token_expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))
        bank_connection.status = 'active'
        bank_connection.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"Successfully refreshed token for bank connection {bank_connection.id}")
        
    def verify_webhook_certificate(self, client_cert):
        """
        Verify the client certificate from GoCardless webhook
        
        Args:
            client_cert: Client certificate from the webhook request
            
        Returns:
            Boolean indicating if certificate is valid
        """
        try:
            # If no client certificate was provided, check if we're in development mode
            if not client_cert:
                # In development, we might want to bypass certificate verification
                if os.environ.get('FLASK_ENV') == 'development':
                    logger.warning("Development mode: Bypassing webhook certificate verification")
                    return True
                else:
                    logger.error("No client certificate provided with webhook")
                    return False
            
            # Check if certificate files exist
            if not self.webhook_cert_path or not self.webhook_key_path:
                logger.error("Webhook certificate or key path not configured")
                return False
            
            if not os.path.exists(self.webhook_cert_path) or not os.path.exists(self.webhook_key_path):
                logger.error("Webhook certificate or key file not found")
                return False
            
            # In a production environment, we'd validate the certificate against our CA
            # For now, we'll just log the certificate details and return True for development
            logger.info(f"Received client certificate: {client_cert[:100]}...")
            
            # TODO: Implement proper certificate validation against GoCardless CA
            # For production, you'd use libraries like PyOpenSSL to validate the certificate
            
            return True
        except Exception as e:
            logger.error(f"Error verifying webhook certificate: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data):
        """
        Process a webhook event from GoCardless
        
        Args:
            webhook_data: Webhook payload from GoCardless
            
        Returns:
            Dictionary with processing result
        """
        try:
            logger.info(f"Processing GoCardless webhook: {json.dumps(webhook_data)[:200]}...")
            
            # Extract event type and resource information
            event_type = webhook_data.get('event_type')
            resource_type = webhook_data.get('resource_type')
            resource_id = webhook_data.get('resource_id')
            
            if not event_type or not resource_type or not resource_id:
                logger.error("Invalid webhook format: missing required fields")
                return {"success": False, "message": "Invalid webhook format"}
            
            logger.info(f"Webhook event: {event_type}, resource: {resource_type}, id: {resource_id}")
            
            # Handle different event types
            if resource_type == 'transactions' and event_type == 'created':
                # New transaction created, fetch and store it
                self._process_transaction_webhook(webhook_data)
                
            elif resource_type == 'accounts' and event_type == 'updated':
                # Account updated, update our records
                self._process_account_update_webhook(webhook_data)
                
            elif resource_type == 'connections' and event_type == 'revoked':
                # Connection revoked, update our status
                self._process_connection_revoked_webhook(webhook_data)
            
            # Log webhook processing
            logger.info(f"Successfully processed webhook: {event_type} - {resource_type}")
            
            return {
                "success": True, 
                "message": f"Processed {event_type} event for {resource_type}"
            }
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _process_transaction_webhook(self, webhook_data):
        """Process a transaction-related webhook event"""
        # Extract relevant transaction data
        transaction_data = webhook_data.get('resource_data', {})
        transaction_id = transaction_data.get('id')
        account_id = transaction_data.get('account_id')
        
        if not transaction_id or not account_id:
            logger.error("Invalid transaction webhook: missing required fields")
            return
        
        # Check if transaction already exists
        existing = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if existing:
            logger.info(f"Transaction {transaction_id} already exists, skipping")
            return
        
        # Find the bank connection for this account
        bank_connection = BankConnection.query.filter_by(account_id=account_id).first()
        if not bank_connection:
            logger.error(f"No bank connection found for account {account_id}")
            return
        
        # Create new transaction record
        try:
            transaction = Transaction(
                transaction_id=transaction_id,
                bank_id=bank_connection.bank_id,
                bank_name=bank_connection.bank_name,
                account_id=account_id,
                account_name=bank_connection.account_name,
                amount=float(transaction_data.get('amount', 0)),
                currency=transaction_data.get('currency', 'GBP'),
                description=transaction_data.get('description', ''),
                reference=transaction_data.get('reference', ''),
                transaction_date=datetime.strptime(transaction_data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Added new transaction from webhook: {transaction_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error storing transaction from webhook: {str(e)}")
    
    def _process_account_update_webhook(self, webhook_data):
        """Process an account update webhook event"""
        # Extract relevant account data
        account_data = webhook_data.get('resource_data', {})
        account_id = account_data.get('id')
        
        if not account_id:
            logger.error("Invalid account webhook: missing account ID")
            return
        
        # Find related bank connections
        bank_connections = BankConnection.query.filter_by(account_id=account_id).all()
        
        if not bank_connections:
            logger.error(f"No bank connections found for account {account_id}")
            return
        
        # Update account information if needed
        for connection in bank_connections:
            # Update any relevant fields that might have changed
            if 'name' in account_data and account_data['name']:
                connection.account_name = account_data['name']
            
            connection.updated_at = datetime.now()
        
        db.session.commit()
        logger.info(f"Updated bank connection details for account {account_id}")
    
    def _process_connection_revoked_webhook(self, webhook_data):
        """Process a connection revoked webhook event"""
        # Extract relevant connection data
        connection_data = webhook_data.get('resource_data', {})
        account_id = connection_data.get('account_id')
        
        if not account_id:
            logger.error("Invalid connection webhook: missing account ID")
            return
        
        # Find related bank connections
        bank_connections = BankConnection.query.filter_by(account_id=account_id).all()
        
        if not bank_connections:
            logger.error(f"No bank connections found for account {account_id}")
            return
        
        # Update connection status to revoked
        for connection in bank_connections:
            connection.status = 'revoked'
            connection.updated_at = datetime.now()
        
        db.session.commit()
        logger.info(f"Marked bank connection as revoked for account {account_id}")
