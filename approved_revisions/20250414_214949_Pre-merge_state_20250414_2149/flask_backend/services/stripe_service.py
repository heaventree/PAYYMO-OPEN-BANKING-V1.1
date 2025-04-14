"""
Stripe service for multi-tenant SaaS architecture
Handles Stripe account connection, payment retrieval, and reconciliation
"""
import os
import logging
import stripe
from datetime import datetime, timedelta
from flask import current_app
from flask_backend.models.integrations import Integration, IntegrationType
from flask_backend.models.financial import StandardizedTransaction, PaymentMethod

# Setup logging
logger = logging.getLogger(__name__)

class StripeService:
    """Service for interacting with the Stripe API in a multi-tenant context"""
    
    def __init__(self, tenant_id=None):
        """
        Initialize the Stripe service
        
        Args:
            tenant_id: ID of the tenant (if None, uses platform-level API key)
        """
        self.tenant_id = tenant_id
        
        # Set the API key - use tenant-specific key if available, otherwise use platform key
        if tenant_id:
            integration = Integration.query.filter_by(
                tenant_id=tenant_id,
                type=IntegrationType.STRIPE.value,
                is_active=True
            ).first()
            
            if integration and integration.credentials.get('secret_key'):
                self.api_key = integration.credentials['secret_key']
            else:
                self.api_key = os.environ.get('STRIPE_SECRET_KEY')
        else:
            self.api_key = os.environ.get('STRIPE_SECRET_KEY')
            
        # Initialize Stripe with the API key
        stripe.api_key = self.api_key
        
    def check_health(self):
        """Check the health of the Stripe API"""
        try:
            # Simple API call to check if the API key works
            stripe.Balance.retrieve()
            return {
                "status": "healthy",
                "message": "Stripe API is working properly"
            }
        except Exception as e:
            logger.error(f"Stripe API health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Stripe API is not working: {str(e)}"
            }
            
    def get_authorization_url(self, redirect_uri, state=None):
        """
        Generate Stripe authorization URL for OAuth flow
        
        Args:
            redirect_uri: Callback URL after authorization
            state: State parameter for OAuth security
            
        Returns:
            Authorization URL string
        """
        client_id = os.environ.get('STRIPE_CLIENT_ID')
        if not client_id:
            raise ValueError("Stripe client ID not configured")
            
        # Build OAuth URL
        url = f"https://connect.stripe.com/oauth/authorize"
        params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "read_write",
            "redirect_uri": redirect_uri
        }
        
        if state:
            params["state"] = state
            
        # Convert params to URL query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{url}?{query_string}"
    
    def process_callback(self, code, tenant_id):
        """
        Process OAuth callback from Stripe
        
        Args:
            code: Authorization code from callback
            tenant_id: ID of the tenant connecting their Stripe account
            
        Returns:
            Dictionary with Stripe account information
        """
        try:
            # Exchange authorization code for access token
            response = stripe.OAuth.token({
                'grant_type': 'authorization_code',
                'code': code,
            })
            
            # Extract account details
            account_id = response['stripe_user_id']
            
            # Store temporary API key to get account details
            temp_api_key = response['access_token']
            
            # Use the temporary key to get account info
            stripe.api_key = temp_api_key
            account = stripe.Account.retrieve(account_id)
            
            # Reset API key
            stripe.api_key = self.api_key
            
            # Create or update the integration record
            integration = Integration.query.filter_by(
                tenant_id=tenant_id,
                type=IntegrationType.STRIPE.value,
                external_id=account_id
            ).first()
            
            if not integration:
                integration = Integration(
                    tenant_id=tenant_id,
                    type=IntegrationType.STRIPE.value,
                    name=f"Stripe: {account.business_profile.name or account.email}",
                    external_id=account_id,
                    status="active",
                    credentials={
                        "access_token": response['access_token'],
                        "refresh_token": response.get('refresh_token'),
                        "scope": response.get('scope', ''),
                        "token_type": response.get('token_type', 'bearer'),
                        "publishable_key": response.get('stripe_publishable_key'),
                        "stripe_user_id": account_id
                    },
                    settings={
                        "account_email": account.email,
                        "account_country": account.country,
                        "account_type": account.type,
                        "business_name": account.business_profile.name,
                        "business_url": account.business_profile.url
                    }
                )
            else:
                # Update existing integration
                integration.status = "active"
                integration.name = f"Stripe: {account.business_profile.name or account.email}"
                integration.credentials = {
                    "access_token": response['access_token'],
                    "refresh_token": response.get('refresh_token'),
                    "scope": response.get('scope', ''),
                    "token_type": response.get('token_type', 'bearer'),
                    "publishable_key": response.get('stripe_publishable_key'),
                    "stripe_user_id": account_id
                }
                integration.settings = {
                    "account_email": account.email,
                    "account_country": account.country,
                    "account_type": account.type,
                    "business_name": account.business_profile.name,
                    "business_url": account.business_profile.url
                }
                
            current_app.extensions['sqlalchemy'].db.session.add(integration)
            current_app.extensions['sqlalchemy'].db.session.commit()
            
            return {
                "success": True,
                "account_id": account_id,
                "account_name": account.business_profile.name or account.email,
                "account_email": account.email,
                "account_country": account.country,
                "integration_id": integration.id
            }
            
        except Exception as e:
            logger.error(f"Error processing Stripe OAuth callback: {str(e)}")
            raise
            
    def fetch_payments(self, integration_id, from_date=None, to_date=None, limit=100):
        """
        Fetch payments from Stripe for a specific account
        
        Args:
            integration_id: ID of the Stripe integration
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Maximum number of payments to retrieve
            
        Returns:
            List of standardized transaction objects
        """
        integration = Integration.query.get(integration_id)
        if not integration or integration.type != IntegrationType.STRIPE.value:
            raise ValueError(f"Invalid Stripe integration ID: {integration_id}")
            
        # Set API key to integration's access token
        stripe.api_key = integration.credentials['access_token']
        
        # Set date filters
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()
            
        # Convert dates to timestamps for Stripe API
        created_after = int(from_date.timestamp())
        created_before = int(to_date.timestamp())
        
        try:
            # Fetch charges from Stripe
            charges = stripe.Charge.list(
                created={'gte': created_after, 'lte': created_before},
                limit=limit,
                expand=['data.customer', 'data.payment_method']
            )
            
            # Convert to standardized transactions
            transactions = []
            
            for charge in charges.data:
                # Create standardized transaction
                transaction = StandardizedTransaction(
                    tenant_id=integration.tenant_id,
                    integration_id=integration.id,
                    source="stripe",
                    source_id=charge.id,
                    amount=charge.amount / 100,  # Convert from cents
                    currency=charge.currency.upper(),
                    status=charge.status,
                    description=charge.description,
                    reference=charge.id,
                    transaction_date=datetime.fromtimestamp(charge.created),
                    transaction_metadata={
                        "payment_method_type": charge.payment_method_details.type if charge.payment_method_details else None,
                        "payment_method_id": charge.payment_method,
                        "customer_id": charge.customer,
                        "receipt_url": charge.receipt_url,
                        "receipt_number": charge.receipt_number,
                        "payment_intent": charge.payment_intent,
                        "failure_code": charge.failure_code,
                        "failure_message": charge.failure_message
                    }
                )
                
                transactions.append(transaction)
                
            # Reset API key
            stripe.api_key = self.api_key
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching Stripe payments: {str(e)}")
            # Reset API key
            stripe.api_key = self.api_key
            raise
            
    def get_account_balance(self, integration_id):
        """
        Get the current balance for a Stripe account
        
        Args:
            integration_id: ID of the Stripe integration
            
        Returns:
            Dictionary with balance information
        """
        integration = Integration.query.get(integration_id)
        if not integration or integration.type != IntegrationType.STRIPE.value:
            raise ValueError(f"Invalid Stripe integration ID: {integration_id}")
            
        # Set API key to integration's access token
        stripe.api_key = integration.credentials['access_token']
        
        try:
            # Fetch balance
            balance = stripe.Balance.retrieve()
            
            # Format the response
            available_balances = {}
            pending_balances = {}
            
            for available in balance.available:
                available_balances[available.currency] = available.amount / 100
                
            for pending in balance.pending:
                pending_balances[pending.currency] = pending.amount / 100
                
            # Reset API key
            stripe.api_key = self.api_key
            
            return {
                "available": available_balances,
                "pending": pending_balances
            }
            
        except Exception as e:
            logger.error(f"Error fetching Stripe balance: {str(e)}")
            # Reset API key
            stripe.api_key = self.api_key
            raise
            
    def get_payment_methods(self, integration_id, customer_id):
        """
        Get payment methods for a customer
        
        Args:
            integration_id: ID of the Stripe integration
            customer_id: Stripe customer ID
            
        Returns:
            List of payment method objects
        """
        integration = Integration.query.get(integration_id)
        if not integration or integration.type != IntegrationType.STRIPE.value:
            raise ValueError(f"Invalid Stripe integration ID: {integration_id}")
            
        # Set API key to integration's access token
        stripe.api_key = integration.credentials['access_token']
        
        try:
            # Fetch payment methods
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            # Convert to standardized payment methods
            result = []
            
            for pm in payment_methods.data:
                # Create or update payment method
                payment_method = PaymentMethod.query.filter_by(
                    tenant_id=integration.tenant_id,
                    integration_id=integration.id,
                    source="stripe",
                    source_id=pm.id,
                    customer_id=customer_id
                ).first()
                
                if not payment_method:
                    payment_method = PaymentMethod(
                        tenant_id=integration.tenant_id,
                        integration_id=integration.id,
                        customer_id=customer_id,
                        source="stripe",
                        source_id=pm.id,
                        method_type=pm.type,
                        is_default=pm.metadata.get('default', False),
                        last_digits=pm.card.last4 if pm.type == 'card' else None,
                        expiry_month=pm.card.exp_month if pm.type == 'card' else None,
                        expiry_year=pm.card.exp_year if pm.type == 'card' else None,
                        status="active",
                        billing_details={
                            "name": pm.billing_details.name,
                            "email": pm.billing_details.email,
                            "phone": pm.billing_details.phone,
                            "address": pm.billing_details.address.to_dict() if pm.billing_details.address else None
                        }
                    )
                    current_app.extensions['sqlalchemy'].db.session.add(payment_method)
                else:
                    # Update existing payment method
                    payment_method.method_type = pm.type
                    payment_method.is_default = pm.metadata.get('default', False)
                    if pm.type == 'card':
                        payment_method.last_digits = pm.card.last4
                        payment_method.expiry_month = pm.card.exp_month
                        payment_method.expiry_year = pm.card.exp_year
                    payment_method.status = "active"
                    payment_method.billing_details = {
                        "name": pm.billing_details.name,
                        "email": pm.billing_details.email,
                        "phone": pm.billing_details.phone,
                        "address": pm.billing_details.address.to_dict() if pm.billing_details.address else None
                    }
                
                result.append(payment_method)
                
            current_app.extensions['sqlalchemy'].db.session.commit()
            
            # Reset API key
            stripe.api_key = self.api_key
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Stripe payment methods: {str(e)}")
            # Reset API key
            stripe.api_key = self.api_key
            raise
            
    def create_checkout_session(self, integration_id, line_items, success_url, cancel_url, customer_id=None):
        """
        Create a Stripe Checkout session
        
        Args:
            integration_id: ID of the Stripe integration
            line_items: List of items to charge for
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            customer_id: Optional Stripe customer ID
            
        Returns:
            Checkout session URL
        """
        integration = Integration.query.get(integration_id)
        if not integration or integration.type != IntegrationType.STRIPE.value:
            raise ValueError(f"Invalid Stripe integration ID: {integration_id}")
            
        # Set API key to integration's access token
        stripe.api_key = integration.credentials['access_token']
        
        try:
            # Create checkout session
            session_params = {
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
            }
            
            if customer_id:
                session_params['customer'] = customer_id
                
            session = stripe.checkout.Session.create(**session_params)
            
            # Reset API key
            stripe.api_key = self.api_key
            
            return {
                'id': session.id,
                'url': session.url
            }
            
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {str(e)}")
            # Reset API key
            stripe.api_key = self.api_key
            raise