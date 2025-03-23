"""
Stripe integration service for connecting and retrieving transaction data from Stripe accounts
Handles OAuth flows, transaction retrieval, and account connection management
Focuses purely on retrieving transaction records for reconciliation, not on payment processing
"""
import os
import json
import logging
import stripe
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import current_app, url_for
from flask_backend.app import db
from flask_backend.models import WhmcsInstance, StripeConnection, StripePayment

logger = logging.getLogger(__name__)

class StripeService:
    """Service for interacting with the Stripe API"""
    
    def __init__(self):
        """Initialize the Stripe service with API credentials"""
        # Set Stripe API key from environment
        self.api_key = os.environ.get('STRIPE_SECRET_KEY')
        self.client_id = os.environ.get('STRIPE_CLIENT_ID')
        self.base_url = 'https://api.stripe.com/v1'
        self.connect_base_url = 'https://connect.stripe.com/oauth'
        
        # Initialize Stripe library if API key is available
        if self.api_key:
            stripe.api_key = self.api_key
    
    def check_health(self):
        """Check the health of the Stripe API"""
        try:
            # Make a simple API call to check if Stripe is responsive
            balance = stripe.Balance.retrieve()
            return {
                'status': 'healthy',
                'message': 'Stripe API is responsive',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Stripe API health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'message': f"Stripe API health check failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_authorization_url(self, domain, redirect_uri):
        """
        Generate Stripe authorization URL for OAuth flow
        
        Args:
            domain: WHMCS instance domain
            redirect_uri: Callback URL after authorization
            
        Returns:
            Authorization URL string
        """
        if not self.client_id:
            raise ValueError("Stripe client ID not configured")
        
        # Generate a unique state parameter to prevent CSRF
        state = f"{domain}:{redirect_uri}"
        
        # Build params for the authorization URL
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'read_write',  # Access to manage account and read payments
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        # Build the URL
        url = f"{self.connect_base_url}/authorize?{urlencode(params)}"
        return url
    
    def process_callback(self, code, state):
        """
        Process OAuth callback from Stripe
        
        Args:
            code: Authorization code from callback
            state: State parameter from callback
            
        Returns:
            Dictionary with Stripe account information
        """
        if not self.api_key or not self.client_id:
            raise ValueError("Stripe API credentials not configured")
        
        # Exchange authorization code for access token
        response = requests.post(
            f"{self.connect_base_url}/token",
            data={
                'client_secret': self.api_key,
                'client_id': self.client_id,
                'grant_type': 'authorization_code',
                'code': code
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to exchange code for token: {response.text}")
            raise Exception(f"Failed to exchange code for token: {response.text}")
        
        # Parse the response
        token_data = response.json()
        
        # Extract account info
        account_id = token_data.get('stripe_user_id')
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        publishable_key = token_data.get('stripe_publishable_key')
        token_expires_at = None
        
        if token_data.get('expires_in'):
            token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in'))
        
        # Get detailed account information
        account_info = self._get_account_info(access_token, account_id)
        
        # Parse domain from state
        domain = state.split(':')[0] if ':' in state else None
        
        if not domain:
            raise ValueError("Invalid state parameter")
        
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Create or update Stripe connection
        stripe_connection = StripeConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not stripe_connection:
            stripe_connection = StripeConnection(
                whmcs_instance_id=whmcs_instance.id,
                account_id=account_id,
                account_name=account_info.get('business_name') or account_info.get('display_name'),
                account_email=account_info.get('email'),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                publishable_key=publishable_key,
                account_type=account_info.get('type', 'standard'),
                account_country=account_info.get('country')
            )
            db.session.add(stripe_connection)
        else:
            stripe_connection.access_token = access_token
            stripe_connection.refresh_token = refresh_token
            stripe_connection.token_expires_at = token_expires_at
            stripe_connection.publishable_key = publishable_key
            stripe_connection.status = 'active'
            stripe_connection.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'account_id': account_id,
            'account_name': stripe_connection.account_name,
            'account_type': stripe_connection.account_type,
            'country': stripe_connection.account_country
        }
    
    def _get_account_info(self, access_token, account_id):
        """
        Get Stripe account information using the access token
        
        Args:
            access_token: OAuth access token
            account_id: Stripe account ID
            
        Returns:
            Dictionary with account details
        """
        try:
            # Use the library with the access token
            stripe.api_key = access_token
            account = stripe.Account.retrieve(account_id)
            return account
        except Exception as e:
            logger.error(f"Failed to get account info: {str(e)}")
            raise
    
    def fetch_payments(self, domain, account_id, from_date=None, to_date=None):
        """
        Fetch payments from Stripe for a specific account
        
        Args:
            domain: WHMCS instance domain
            account_id: Stripe account ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            
        Returns:
            List of payments
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Find the Stripe connection
        connection = StripeConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not connection:
            raise ValueError(f"Stripe connection not found for account: {account_id}")
        
        # Check if token is expired and refresh if needed
        if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
            self._refresh_token(connection)
        
        # Convert date strings to timestamp if provided
        created_params = {}
        
        if from_date:
            from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
            created_params['gte'] = int(from_datetime.timestamp())
        
        if to_date:
            to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
            # Set to end of day
            to_datetime = to_datetime.replace(hour=23, minute=59, second=59)
            created_params['lte'] = int(to_datetime.timestamp())
        
        try:
            # Use the connection's access token
            stripe.api_key = connection.access_token
            
            # Fetch payments
            params = {
                'limit': 100  # Maximum allowed by Stripe
            }
            
            if created_params:
                params['created'] = created_params
            
            payments = stripe.PaymentIntent.list(**params)
            
            # Process and store payments
            stored_payments = []
            
            for payment in payments.data:
                # Try to find an existing payment record
                existing = StripePayment.query.filter_by(payment_id=payment.id).first()
                
                if existing:
                    continue
                
                # Get customer info if available
                customer_id = payment.customer
                customer_name = None
                customer_email = None
                
                if customer_id:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                        customer_name = customer.name
                        customer_email = customer.email
                    except Exception as e:
                        logger.warning(f"Could not retrieve customer {customer_id}: {str(e)}")
                
                # Create payment record
                payment_record = StripePayment(
                    stripe_connection_id=connection.id,
                    payment_id=payment.id,
                    customer_id=customer_id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    amount=payment.amount / 100.0,  # Convert from cents
                    currency=payment.currency.upper(),
                    description=payment.description,
                    payment_metadata=json.dumps(payment.metadata),
                    payment_date=datetime.fromtimestamp(payment.created),
                    payment_status=payment.status,
                    payment_method=payment.payment_method_types[0] if payment.payment_method_types else None
                )
                
                db.session.add(payment_record)
                stored_payments.append(payment_record)
            
            db.session.commit()
            
            return {
                'success': True,
                'payments': [
                    {
                        'id': p.id,
                        'payment_id': p.payment_id,
                        'amount': p.amount,
                        'currency': p.currency,
                        'payment_date': p.payment_date.isoformat(),
                        'customer_name': p.customer_name,
                        'status': p.payment_status
                    } for p in stored_payments
                ],
                'total': len(stored_payments)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch payments: {str(e)}")
            db.session.rollback()
            raise
    
    def get_account_balance(self, domain, account_id):
        """
        Get the current balance for a Stripe account
        
        Args:
            domain: WHMCS instance domain
            account_id: Stripe account ID
            
        Returns:
            Dictionary with balance information
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise ValueError(f"WHMCS instance not found for domain: {domain}")
        
        # Find the Stripe connection
        connection = StripeConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not connection:
            raise ValueError(f"Stripe connection not found for account: {account_id}")
        
        # Check if token is expired and refresh if needed
        if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
            self._refresh_token(connection)
        
        try:
            # Use the connection's access token
            stripe.api_key = connection.access_token
            
            # Get the balance
            balance = stripe.Balance.retrieve()
            
            # Format balance data
            available = []
            pending = []
            
            for b in balance.available:
                available.append({
                    'amount': b.amount / 100.0,  # Convert from cents
                    'currency': b.currency.upper()
                })
            
            for b in balance.pending:
                pending.append({
                    'amount': b.amount / 100.0,  # Convert from cents
                    'currency': b.currency.upper()
                })
            
            return {
                'success': True,
                'available': available,
                'pending': pending
            }
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            raise
            
    def generate_test_data(self, domain, account_id=None, num_payments=10):
        """
        Generate test payment data for Stripe 
        
        Args:
            domain: WHMCS instance domain
            account_id: Optional Stripe account ID (if None, creates a test account)
            num_payments: Number of payments to generate
            
        Returns:
            Dictionary with generated data information
        """
        try:
            # Find the WHMCS instance
            whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
            
            if not whmcs_instance:
                raise ValueError(f"WHMCS instance not found for domain: {domain}")
            
            # Create a test Stripe connection if account_id not provided
            if not account_id:
                # Check if a test connection already exists
                test_connection = StripeConnection.query.filter_by(
                    whmcs_instance_id=whmcs_instance.id,
                    account_id='test_acct_1'
                ).first()
                
                if not test_connection:
                    test_connection = StripeConnection(
                        whmcs_instance_id=whmcs_instance.id,
                        account_id='test_acct_1',
                        account_name='Test Stripe Account',
                        account_email='test@example.com',
                        access_token='test_access_token',
                        refresh_token='test_refresh_token',
                        token_expires_at=datetime.utcnow() + timedelta(days=30),
                        publishable_key='pk_test_123456789',
                        status='active',
                        account_type='standard',
                        account_country='US'
                    )
                    db.session.add(test_connection)
                    db.session.commit()
                    logger.info(f"Created test Stripe connection for {domain}")
                
                stripe_connection = test_connection
            else:
                # Find the specified Stripe connection
                stripe_connection = StripeConnection.query.filter_by(
                    whmcs_instance_id=whmcs_instance.id,
                    account_id=account_id
                ).first()
                
                if not stripe_connection:
                    raise ValueError(f"Stripe connection not found for account: {account_id}")
            
            # Generate random payments
            from random import randint, uniform, choice
            import string
            import json
            
            created_payments = []
            currencies = ['USD', 'EUR', 'GBP']
            payment_methods = ['card', 'bank_transfer', 'sepa_debit']
            statuses = ['succeeded', 'pending', 'refunded']
            
            for i in range(num_payments):
                # Generate random payment ID
                payment_id = 'pi_' + ''.join(choice(string.ascii_letters + string.digits) for _ in range(24))
                
                # Check if payment already exists
                existing = StripePayment.query.filter_by(payment_id=payment_id).first()
                if existing:
                    continue
                
                # Random amount between $10 and $1000
                amount = round(uniform(10, 1000), 2)
                
                # Random date in the last 30 days
                days_ago = randint(0, 30)
                payment_date = datetime.utcnow() - timedelta(days=days_ago)
                
                # Create customer ID and other fields
                customer_id = 'cus_' + ''.join(choice(string.ascii_letters + string.digits) for _ in range(14))
                currency = choice(currencies)
                payment_method = choice(payment_methods)
                status = choice(statuses)
                
                # Create metadata
                metadata = {
                    'invoice_id': f"INVOICE-{randint(10000, 99999)}",
                    'customer_ref': f"CUST-{randint(1000, 9999)}",
                    'source': 'test_data'
                }
                
                # Create the payment record
                payment = StripePayment(
                    stripe_connection_id=stripe_connection.id,
                    payment_id=payment_id,
                    customer_id=customer_id,
                    customer_name=f"Test Customer {i+1}",
                    customer_email=f"customer{i+1}@example.com",
                    amount=amount,
                    currency=currency,
                    description=f"Test payment {i+1}",
                    payment_metadata=json.dumps(metadata),
                    payment_date=payment_date,
                    payment_status=status,
                    payment_method=payment_method
                )
                
                db.session.add(payment)
                created_payments.append(payment)
            
            db.session.commit()
            
            return {
                'success': True,
                'connection_id': stripe_connection.id,
                'account_id': stripe_connection.account_id,
                'payments_created': len(created_payments),
                'payments': [
                    {
                        'id': p.id,
                        'payment_id': p.payment_id,
                        'amount': p.amount,
                        'currency': p.currency,
                        'payment_date': p.payment_date.isoformat(),
                        'customer_name': p.customer_name,
                        'status': p.payment_status
                    } for p in created_payments
                ]
            }
        
        except Exception as e:
            logger.error(f"Failed to generate test data: {str(e)}")
            db.session.rollback()
            raise
    
    def _refresh_token(self, stripe_connection):
        """
        Refresh an expired OAuth token
        
        Args:
            stripe_connection: StripeConnection object with expired token
            
        Returns:
            None (updates the stripe_connection object)
        """
        if not stripe_connection.refresh_token:
            logger.warning(f"No refresh token available for Stripe connection {stripe_connection.id}")
            return
        
        try:
            response = requests.post(
                f"{self.connect_base_url}/token",
                data={
                    'client_secret': self.api_key,
                    'client_id': self.client_id,
                    'grant_type': 'refresh_token',
                    'refresh_token': stripe_connection.refresh_token
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to refresh token: {response.text}")
                stripe_connection.status = 'expired'
                db.session.commit()
                return
            
            # Parse the response
            token_data = response.json()
            
            # Update connection
            stripe_connection.access_token = token_data.get('access_token')
            
            if token_data.get('refresh_token'):
                stripe_connection.refresh_token = token_data.get('refresh_token')
            
            if token_data.get('expires_in'):
                stripe_connection.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in'))
            
            stripe_connection.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            stripe_connection.status = 'expired'
            db.session.commit()