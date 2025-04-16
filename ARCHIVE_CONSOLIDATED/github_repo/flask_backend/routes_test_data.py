"""
Test Data Generation API Routes
Endpoints for generating test data for development and testing purposes
These routes should only be used in development/testing environments
"""
import json
import logging
import random
import string
from datetime import datetime, timedelta

from flask import request, jsonify
from flask_backend.app import app, db
from flask_backend.models import (
    WhmcsInstance, BankConnection, Transaction,
    StripeConnection, StripePayment
)
from flask_backend.utils.error_handler import handle_error, APIError

# Logger
logger = logging.getLogger(__name__)

# ============= Test Data Generation Endpoints =============

@app.route('/api/testing/generate-gocardless-data', methods=['POST'])
def generate_gocardless_test_data():
    """Generate test data for GoCardless transactions"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')  # Must be provided for GoCardless
        num_transactions = int(data.get('num_transactions', 10))
        
        if not license_key or not domain or not account_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", status_code=404)
        
        # Find bank connection
        bank_connection = BankConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not bank_connection:
            # Create a test bank connection if it doesn't exist
            bank_connection = BankConnection(
                whmcs_instance_id=whmcs_instance.id,
                bank_id='test-bank-001',
                bank_name='Test Bank UK',
                account_id=account_id,
                account_name='Test Account',
                access_token='test_access_token',
                refresh_token='test_refresh_token',
                token_expires_at=datetime.now() + timedelta(days=30),
                status='active'
            )
            db.session.add(bank_connection)
            db.session.commit()
            logger.info(f"Created test bank connection for {domain}")
        
        # Generate random transactions
        transactions = []
        for i in range(num_transactions):
            # Generate a unique transaction ID
            transaction_id = 'tr_' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            
            # Generate a random amount between 10.00 and 1000.00
            amount = round(random.uniform(10.0, 1000.0), 2)
            
            # Generate a random date in the last 30 days
            days_ago = random.randint(1, 30)
            transaction_date = datetime.now() - timedelta(days=days_ago)
            
            # Create a fake reference
            reference = f"INV-{random.randint(1000, 9999)}"
            
            # Create a fake description
            description = f"Payment for {random.choice(['hosting', 'domain', 'services', 'support'])}"
            
            # Create the transaction
            transaction = Transaction(
                transaction_id=transaction_id,
                bank_id=bank_connection.bank_id,
                bank_name=bank_connection.bank_name,
                account_id=bank_connection.account_id,
                account_name=bank_connection.account_name,
                amount=amount,
                currency='GBP',
                description=description,
                reference=reference,
                transaction_date=transaction_date,
                created_at=datetime.now()
            )
            
            db.session.add(transaction)
            transactions.append({
                'id': transaction_id,
                'amount': amount,
                'currency': 'GBP',
                'description': description,
                'reference': reference,
                'date': transaction_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        db.session.commit()
        logger.info(f"Generated {len(transactions)} test transactions for account {account_id}")
        
        return jsonify({
            'success': True,
            'transactions_created': len(transactions),
            'transactions': transactions
        })
    except Exception as e:
        return handle_error(e)
        
@app.route('/api/testing/generate-stripe-test-data', methods=['POST'])
def generate_stripe_test_data_extended():
    """Generate test data for Stripe payments"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')  # Must be provided for Stripe
        num_payments = int(data.get('num_payments', 10))
        
        if not license_key or not domain or not account_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", status_code=404)
        
        # Find Stripe connection
        stripe_connection = StripeConnection.query.filter_by(
            whmcs_instance_id=whmcs_instance.id,
            account_id=account_id
        ).first()
        
        if not stripe_connection:
            # Create a test Stripe connection if it doesn't exist
            stripe_connection = StripeConnection(
                whmcs_instance_id=whmcs_instance.id,
                account_id=account_id,
                account_name='Test Stripe Account',
                account_email='test@example.com',
                access_token='test_access_token',
                refresh_token='test_refresh_token',
                token_expires_at=datetime.now() + timedelta(days=30),
                publishable_key='pk_test_' + ''.join(random.choices(string.ascii_letters + string.digits, k=24)),
                status='active',
                account_type='standard',
                account_country='GB'
            )
            db.session.add(stripe_connection)
            db.session.commit()
            logger.info(f"Created test Stripe connection for {domain}")
        
        # Generate random payments
        payments = []
        for i in range(num_payments):
            # Generate a unique payment ID
            payment_id = 'py_' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            
            # Generate a unique customer ID
            customer_id = 'cus_' + ''.join(random.choices(string.ascii_letters + string.digits, k=14))
            
            # Generate a random customer name
            first_names = ['John', 'Jane', 'Mike', 'Sarah', 'Chris', 'Emma', 'David', 'Lisa']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Wilson']
            customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Generate a random customer email
            customer_email = f"{customer_name.lower().replace(' ', '.')}@example.com"
            
            # Generate a random amount between 10.00 and 1000.00
            amount = round(random.uniform(10.0, 1000.0), 2)
            
            # Generate a random date in the last 30 days
            days_ago = random.randint(1, 30)
            payment_date = datetime.now() - timedelta(days=days_ago)
            
            # Create a fake description
            description = f"Stripe payment for {random.choice(['hosting', 'domain', 'services', 'support'])}"
            
            # Create fake metadata
            metadata = {
                'invoice_id': str(random.randint(1000, 9999)),
                'customer_id': str(random.randint(100, 999)),
                'product_id': str(random.randint(1, 50))
            }
            
            # Create the payment
            payment = StripePayment(
                stripe_connection_id=stripe_connection.id,
                payment_id=payment_id,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_email=customer_email,
                amount=amount,
                currency='USD',
                description=description,
                payment_metadata=json.dumps(metadata),
                payment_date=payment_date,
                payment_status=random.choices(['succeeded', 'pending', 'failed'], weights=[0.9, 0.05, 0.05])[0],
                payment_method=random.choice(['card', 'bank_transfer']),
                created_at=datetime.now()
            )
            
            db.session.add(payment)
            payments.append({
                'id': payment_id,
                'customer': customer_name,
                'amount': amount,
                'currency': 'USD',
                'description': description,
                'date': payment_date.strftime('%Y-%m-%d %H:%M:%S'),
                'status': payment.payment_status
            })
        
        db.session.commit()
        logger.info(f"Generated {len(payments)} test Stripe payments for account {account_id}")
        
        return jsonify({
            'success': True,
            'payments_created': len(payments),
            'payments': payments
        })
    except Exception as e:
        return handle_error(e)