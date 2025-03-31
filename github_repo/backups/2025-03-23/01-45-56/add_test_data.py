#!/usr/bin/env python3
"""
Script to add test transaction data to the Payymo database.
This will create a mix of bank and Stripe transactions for testing.
"""
import os
import sys
import json
import random
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index

# Base setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import models - we'll define them here for simplicity
# First, we need license key data
class LicenseKey(db.Model):
    """License key model to validate WHMCS instances"""
    __tablename__ = 'license_keys'

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    status = Column(String(20), default='active')  # active, expired, suspended
    owner_name = Column(String(255))
    owner_email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_verified = Column(DateTime)
    allowed_domains = Column(Text)  # JSON serialized list of allowed domains
    max_banks = Column(Integer, default=5)
    max_transactions = Column(Integer, default=1000)
    features = Column(Text)  # JSON serialized dictionary of features
class WhmcsInstance(db.Model):
    """Details of connected WHMCS instances"""
    __tablename__ = 'whmcs_instances'

    id = Column(Integer, primary_key=True)
    license_key = Column(String(64), nullable=True)
    domain = Column(String(255), nullable=False)
    api_identifier = Column(String(255))
    api_secret = Column(String(255))
    admin_user = Column(String(100))
    webhook_secret = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class BankConnection(db.Model):
    """Bank connection details"""
    __tablename__ = 'bank_connections'

    id = Column(Integer, primary_key=True)
    whmcs_instance_id = Column(Integer, ForeignKey('whmcs_instances.id'))
    bank_id = Column(String(100), nullable=False)
    bank_name = Column(String(100))
    account_id = Column(String(100), nullable=False)
    account_name = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    status = Column(String(20), default='active')  # active, expired, revoked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class StripeConnection(db.Model):
    """Stripe account connection details"""
    __tablename__ = 'stripe_connections'

    id = Column(Integer, primary_key=True)
    whmcs_instance_id = Column(Integer, ForeignKey('whmcs_instances.id'))
    account_id = Column(String(100), nullable=False)
    account_name = Column(String(255))
    account_email = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    publishable_key = Column(String(255))
    status = Column(String(20), default='active')  # active, expired, revoked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    account_type = Column(String(20), default='standard')  # standard, express, custom
    account_country = Column(String(2))

class Transaction(db.Model):
    """Bank transaction data from GoCardless"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(100), unique=True, nullable=False)
    bank_id = Column(String(100))
    bank_name = Column(String(100))
    account_id = Column(String(100))
    account_name = Column(String(255))
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='GBP')
    description = Column(Text)
    reference = Column(String(255))
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class StripePayment(db.Model):
    """Stripe transaction data for reconciliation"""
    __tablename__ = 'stripe_payments'

    id = Column(Integer, primary_key=True)
    stripe_connection_id = Column(Integer, ForeignKey('stripe_connections.id'))
    payment_id = Column(String(100), unique=True, nullable=False)
    customer_id = Column(String(100))
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    description = Column(Text)
    payment_metadata = Column(Text)  # JSON serialized additional data
    payment_date = Column(DateTime, nullable=False)
    payment_status = Column(String(20), default='succeeded')  # succeeded, pending, failed, refunded
    payment_method = Column(String(20))  # card, bank_transfer, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class InvoiceMatch(db.Model):
    """Matches between transactions and WHMCS invoices"""
    __tablename__ = 'invoice_matches'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    whmcs_invoice_id = Column(Integer, nullable=False)
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    match_reason = Column(Text)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", backref="matches")

class StripeInvoiceMatch(db.Model):
    """Matches between Stripe payments and WHMCS invoices"""
    __tablename__ = 'stripe_invoice_matches'

    id = Column(Integer, primary_key=True)
    stripe_payment_id = Column(Integer, ForeignKey('stripe_payments.id'))
    whmcs_invoice_id = Column(Integer, nullable=False)
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    match_reason = Column(Text)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    payment = relationship("StripePayment", backref="matches")

# Data generation helpers
def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def generate_bank_transaction(index):
    """Generate a random bank transaction"""
    banks = [
        {"id": "lloyds_1234", "name": "Lloyds Bank"},
        {"id": "barclays_2345", "name": "Barclays"},
        {"id": "hsbc_3456", "name": "HSBC UK"},
        {"id": "natwest_4567", "name": "NatWest"},
        {"id": "santander_5678", "name": "Santander UK"},
        {"id": "tsb_6789", "name": "TSB Bank"}
    ]
    
    accounts = [
        {"id": "acc_123456", "name": "Business Account"},
        {"id": "acc_234567", "name": "Current Account"},
        {"id": "acc_345678", "name": "Savings Account"}
    ]
    
    descriptions = [
        "Monthly subscription payment",
        "Invoice payment #INV-",
        "Service payment",
        "Product purchase",
        "Recurring payment",
        "Client payment"
    ]
    
    reference_prefixes = ["INV-", "REF-", "PAY-", "TRX-", "ORD-"]
    
    # Select random bank and account
    bank = random.choice(banks)
    account = random.choice(accounts)
    
    # Generate transaction details
    transaction_id = f"trx_{random.randint(10000, 99999)}_{index}"
    amount = round(random.uniform(10.0, 500.0), 2)
    currency = "GBP"
    
    # Date between 30 days ago and today
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    transaction_date = generate_random_date(start_date, end_date)
    
    # Description and reference
    description = random.choice(descriptions)
    if "Invoice" in description:
        description += f"{random.randint(1000, 9999)}"
    
    reference = f"{random.choice(reference_prefixes)}{random.randint(1000, 9999)}"
    
    return Transaction(
        transaction_id=transaction_id,
        bank_id=bank["id"],
        bank_name=bank["name"],
        account_id=account["id"],
        account_name=account["name"],
        amount=amount,
        currency=currency,
        description=description,
        reference=reference,
        transaction_date=transaction_date
    )

def generate_stripe_payment(index, stripe_connection_id=1):
    """Generate a random Stripe payment"""
    payment_methods = ["card", "bank_transfer", "sepa_debit", "sofort"]
    statuses = ["succeeded", "pending", "failed", "refunded"]
    
    customers = [
        {"id": "cus_123456", "name": "John Smith", "email": "john.smith@example.com"},
        {"id": "cus_234567", "name": "Jane Doe", "email": "jane.doe@example.com"},
        {"id": "cus_345678", "name": "Sam Johnson", "email": "sam.johnson@example.com"},
        {"id": "cus_456789", "name": "Sarah Williams", "email": "sarah.williams@example.com"}
    ]
    
    descriptions = [
        "Website subscription",
        "Premium plan upgrade",
        "One-time service fee",
        "Product purchase",
        "Consulting services",
        "Support plan"
    ]
    
    # Select random customer
    customer = random.choice(customers)
    
    # Generate payment details
    payment_id = f"pi_{random.randint(10000, 99999)}_{index}"
    amount = round(random.uniform(20.0, 600.0), 2)
    currency = random.choice(["USD", "EUR", "GBP"])
    
    # Date between 30 days ago and today
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    payment_date = generate_random_date(start_date, end_date)
    
    # Description and metadata
    description = random.choice(descriptions)
    metadata = {
        "order_id": f"order_{random.randint(1000, 9999)}",
        "source": "website",
        "plan": random.choice(["basic", "premium", "enterprise"])
    }
    
    return StripePayment(
        stripe_connection_id=stripe_connection_id,
        payment_id=payment_id,
        customer_id=customer["id"],
        customer_name=customer["name"],
        customer_email=customer["email"],
        amount=amount,
        currency=currency,
        description=description,
        payment_metadata=json.dumps(metadata),
        payment_date=payment_date,
        payment_status=random.choice(statuses),
        payment_method=random.choice(payment_methods)
    )

def add_test_data(bank_transactions=15, stripe_payments=10):
    """Add test data to the database"""
    with app.app_context():
        # First create a test license key if it doesn't exist
        license_key_str = 'TEST-LICENSE-KEY-12345'
        license_key = LicenseKey.query.filter_by(key=license_key_str).first()
        
        if not license_key:
            print("Creating test license key...")
            license_key = LicenseKey(
                key=license_key_str,
                status='active',
                owner_name='Test User',
                owner_email='test@example.com',
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),
                last_verified=datetime.utcnow(),
                allowed_domains=json.dumps(['test-whmcs.example.com']),
                max_banks=10,
                max_transactions=10000,
                features=json.dumps({'premium_support': True, 'advanced_matching': True})
            )
            db.session.add(license_key)
            db.session.flush()  # To get the ID
        
        # Create a test WHMCS instance if it doesn't exist
        instance = WhmcsInstance.query.filter_by(domain='test-whmcs.example.com').first()
        if not instance:
            print("Creating test WHMCS instance...")
            instance = WhmcsInstance(
                license_key=license_key_str,
                domain='test-whmcs.example.com',
                api_identifier='test_api',
                api_secret='test_secret',
                admin_user='admin',
                webhook_secret='test_webhook_secret',
                created_at=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            db.session.add(instance)
            db.session.flush()  # To get the ID
        
        # Create bank connections for the instance
        banks = [
            {"id": "lloyds_1234", "name": "Lloyds Bank"},
            {"id": "barclays_2345", "name": "Barclays"},
            {"id": "hsbc_3456", "name": "HSBC UK"}
        ]
        
        for bank in banks:
            connection = BankConnection.query.filter_by(
                whmcs_instance_id=instance.id,
                bank_id=bank["id"]
            ).first()
            
            if not connection:
                print(f"Creating bank connection: {bank['name']}...")
                connection = BankConnection(
                    whmcs_instance_id=instance.id,
                    bank_id=bank["id"],
                    bank_name=bank["name"],
                    account_id=f"acc_{random.randint(10000, 99999)}",
                    account_name="Test Account",
                    access_token="test_access_token",
                    refresh_token="test_refresh_token",
                    token_expires_at=datetime.utcnow() + timedelta(days=30),
                    status='active',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(connection)
        
        # Create a stripe connection for the instance
        stripe_connection = StripeConnection.query.filter_by(
            whmcs_instance_id=instance.id
        ).first()
        
        if not stripe_connection:
            print("Creating Stripe connection...")
            stripe_connection = StripeConnection(
                whmcs_instance_id=instance.id,
                account_id=f"acct_{random.randint(10000, 99999)}",
                account_name="Test Stripe Account",
                account_email="stripe@example.com",
                access_token="test_access_token",
                refresh_token="test_refresh_token",
                token_expires_at=datetime.utcnow() + timedelta(days=30),
                publishable_key="pk_test_123456",
                status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                account_type='standard',
                account_country='US'
            )
            db.session.add(stripe_connection)
            db.session.flush()  # To get the ID
            
        # Now we can safely add bank transactions
        print(f"Creating {bank_transactions} bank transactions...")
        bank_txns = []
        for i in range(bank_transactions):
            transaction = generate_bank_transaction(i)
            db.session.add(transaction)
            bank_txns.append(transaction)
        
        # Add stripe payments
        print(f"Creating {stripe_payments} Stripe payments...")
        stripe_pymnts = []
        for i in range(stripe_payments):
            payment = generate_stripe_payment(i, stripe_connection.id)
            db.session.add(payment)
            stripe_pymnts.append(payment)
        
        # Make sure we flush to get the IDs for our transactions and payments
        db.session.flush()
        
        # Randomly match some of the bank transactions to invoices
        print("Creating invoice matches for bank transactions...")
        bank_match_count = random.randint(5, min(10, bank_transactions))
        for i in range(bank_match_count):
            # Select a random transaction
            transaction = random.choice(bank_txns)
            
            # Generate a random WHMCS invoice ID
            invoice_id = random.randint(1000, 9999)
            
            # Generate confidence score between 0.6 and 0.95
            confidence = round(random.uniform(0.6, 0.95), 2)
            
            # Set a random status with higher chance of 'approved'
            status_options = ['pending', 'approved', 'approved', 'approved', 'rejected']
            status = random.choice(status_options)
            
            # Create a match reason
            reason = "Match based on: "
            if random.random() > 0.3:
                reason += "Amount matches exactly. "
            if random.random() > 0.4:
                reason += "Reference contains invoice number. "
            if random.random() > 0.5:
                reason += "Transaction date close to invoice date. "
            
            match = InvoiceMatch(
                transaction_id=transaction.id,
                whmcs_invoice_id=invoice_id,
                confidence=confidence,
                match_reason=reason,
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(match)
        
        # Randomly match some Stripe payments to invoices
        print("Creating invoice matches for Stripe payments...")
        stripe_match_count = random.randint(3, min(8, stripe_payments))
        for i in range(stripe_match_count):
            # Select a random payment
            payment = random.choice(stripe_pymnts)
            
            # Only match successful payments
            if payment.payment_status != 'succeeded':
                continue
                
            # Generate a random WHMCS invoice ID
            invoice_id = random.randint(1000, 9999)
            
            # Generate confidence score between 0.7 and 0.98
            confidence = round(random.uniform(0.7, 0.98), 2)
            
            # Set a random status with higher chance of 'approved'
            status_options = ['pending', 'approved', 'approved', 'approved', 'rejected']
            status = random.choice(status_options)
            
            # Create a match reason
            reason = "Match based on: "
            if random.random() > 0.2:
                reason += "Amount matches exactly. "
            if random.random() > 0.3:
                reason += "Metadata contains invoice reference. "
            if random.random() > 0.4:
                reason += "Customer email matches client email. "
            
            match = StripeInvoiceMatch(
                stripe_payment_id=payment.id,
                whmcs_invoice_id=invoice_id,
                confidence=confidence,
                match_reason=reason,
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(match)
        
        print("Committing to database...")
        db.session.commit()
        print("Done!")

if __name__ == "__main__":
    # Get number of transactions to add from command line, or use defaults
    bank_count = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    stripe_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    add_test_data(bank_count, stripe_count)