"""
Test Configuration for Payymo

This file contains pytest fixtures and configuration for testing the Payymo application.
"""
import os
import pytest
from datetime import datetime, timedelta
from flask_backend.app import app, db
from flask_backend.models import (
    LicenseKey, WhmcsInstance, BankConnection, 
    Transaction, InvoiceMatch, StripeConnection, 
    StripePayment, StripeInvoiceMatch, ApiLog
)

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    # Configure the app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Create the test client
    with app.test_client() as client:
        # Create tables in the test database
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def license_key():
    """Create a test license key"""
    with app.app_context():
        key = LicenseKey(
            key="TEST-LICENSE-KEY-12345",
            status="active",
            owner_name="Test User",
            owner_email="test@example.com",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            last_verified=datetime.utcnow(),
            allowed_domains='["test.example.com", "dev.example.com"]',
            max_banks=5,
            max_transactions=1000,
            features='{"feature1": true, "feature2": false}'
        )
        db.session.add(key)
        db.session.commit()
        return key

@pytest.fixture
def whmcs_instance(license_key):
    """Create a test WHMCS instance"""
    with app.app_context():
        instance = WhmcsInstance(
            license_key=license_key.key,
            domain="test.example.com",
            api_identifier="test_api",
            api_secret="test_secret",
            admin_user="admin",
            webhook_secret="test_webhook_secret",
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.session.add(instance)
        db.session.commit()
        return instance

@pytest.fixture
def bank_connection(whmcs_instance):
    """Create a test bank connection"""
    with app.app_context():
        connection = BankConnection(
            whmcs_instance_id=whmcs_instance.id,
            bank_id="test_bank",
            bank_name="Test Bank",
            account_id="test_account",
            account_name="Test Account",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_expires_at=datetime.utcnow() + timedelta(days=30),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(connection)
        db.session.commit()
        return connection

@pytest.fixture
def transaction(bank_connection):
    """Create a test transaction"""
    with app.app_context():
        transaction = Transaction(
            transaction_id="test_transaction_001",
            bank_id=bank_connection.bank_id,
            bank_name=bank_connection.bank_name,
            account_id=bank_connection.account_id,
            account_name=bank_connection.account_name,
            amount=100.00,
            currency="GBP",
            description="Test Transaction",
            reference="INV-001",
            transaction_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

@pytest.fixture
def stripe_connection(whmcs_instance):
    """Create a test Stripe connection"""
    with app.app_context():
        connection = StripeConnection(
            whmcs_instance_id=whmcs_instance.id,
            account_id="acct_test123",
            account_name="Test Stripe Account",
            account_email="stripe@example.com",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_expires_at=datetime.utcnow() + timedelta(days=30),
            publishable_key="pk_test_123",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            account_type="standard",
            account_country="US"
        )
        db.session.add(connection)
        db.session.commit()
        return connection

@pytest.fixture
def stripe_payment(stripe_connection):
    """Create a test Stripe payment"""
    with app.app_context():
        payment = StripePayment(
            stripe_connection_id=stripe_connection.id,
            payment_id="py_test123",
            customer_id="cus_test123",
            customer_name="Test Customer",
            customer_email="customer@example.com",
            amount=100.00,
            currency="USD",
            description="Test Payment",
            payment_metadata='{"invoice_id": "INV-001"}',
            payment_date=datetime.utcnow(),
            payment_status="succeeded",
            payment_method="card",
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
        return payment