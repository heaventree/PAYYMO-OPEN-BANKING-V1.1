import os
import json
import uuid
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask_backend.app import db
from flask_backend.models import BankConnection, WhmcsInstance, Transaction, ApiLog

logger = logging.getLogger(__name__)

class GoCardlessService:
    """Service for interacting with the GoCardless Open Banking API"""
    
    def __init__(self):
        # Get API credentials from environment
        self.client_id = os.environ.get('GOCARDLESS_CLIENT_ID')
        self.client_secret = os.environ.get('GOCARDLESS_CLIENT_SECRET')
        self.api_base_url = 'https://api.gocardless.com/open-banking'
        self.auth_url = 'https://auth.gocardless.com/oauth/authorize'
        self.token_url = 'https://auth.gocardless.com/oauth/token'
        
        # Dictionary to store state parameters for OAuth flow
        self.oauth_states = {}
    
    def check_health(self):
        """Check the health of the GoCardless API"""
        try:
            # Perform a simple API request to check connectivity
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_base_url}/institutions",
                headers=headers
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GoCardless health check failed: {str(e)}")
            return False
    
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
            raise ValueError("Failed to exchange authorization code for token")
        
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
            'Accept': 'application/json'
        }
        
        response = requests.get(
            f"{self.api_base_url}/accounts",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get bank account info: {response.text}")
            raise ValueError("Failed to get bank account information")
        
        data = response.json()
        
        if not data.get('accounts') or not len(data['accounts']):
            raise ValueError("No bank accounts found")
        
        account = data['accounts'][0]
        
        return {
            'account_id': account['id'],
            'bank_id': account['institution_id'],
            'bank_name': account['institution_name'],
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
            'Accept': 'application/json'
        }
        
        params = {
            'from_date': from_date,
            'to_date': to_date
        }
        
        response = requests.get(
            f"{self.api_base_url}/accounts/{account_id}/transactions",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch transactions: {response.text}")
            raise ValueError("Failed to fetch transactions from GoCardless")
        
        transactions_data = response.json().get('transactions', [])
        
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
            bank_connection.status = 'expired'
            db.session.commit()
            raise ValueError("Failed to refresh access token")
        
        tokens = token_response.json()
        
        # Update the bank connection with new tokens
        bank_connection.access_token = tokens['access_token']
        bank_connection.refresh_token = tokens.get('refresh_token', bank_connection.refresh_token)
        bank_connection.token_expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))
        bank_connection.status = 'active'
        bank_connection.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"Successfully refreshed token for bank connection {bank_connection.id}")
