"""
Legacy models for backward compatibility
These models maintain compatibility with existing code while we transition to the new architecture
"""
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

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
    
    def __repr__(self):
        return f"<LicenseKey {self.key}>"

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
    
    # Relationships
    bank_connections = relationship("BankConnection", back_populates="whmcs_instance")
    stripe_connections = relationship("StripeConnection", back_populates="whmcs_instance")
    
    def __repr__(self):
        return f"<WhmcsInstance {self.domain}>"

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
    
    # Relationship
    whmcs_instance = relationship("WhmcsInstance", back_populates="bank_connections")
    
    def __repr__(self):
        return f"<BankConnection {self.bank_name} - {self.account_name}>"

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
    
    # Relationship
    whmcs_instance = relationship("WhmcsInstance", back_populates="stripe_connections")
    
    def __repr__(self):
        return f"<StripeConnection {self.account_name}>"

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
    
    # Relationships
    matches = relationship("InvoiceMatch", back_populates="transaction")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id} {self.amount} {self.currency}>"

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
    
    # Relationship
    stripe_connection = relationship("StripeConnection", backref="payments")
    matches = relationship("StripeInvoiceMatch", back_populates="payment")
    
    def __repr__(self):
        return f"<StripePayment {self.payment_id} {self.amount} {self.currency}>"

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
    
    # Relationship
    transaction = relationship("Transaction", back_populates="matches")
    
    def __repr__(self):
        return f"<InvoiceMatch Transaction {self.transaction_id} - Invoice {self.whmcs_invoice_id}>"

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
    
    # Relationship
    payment = relationship("StripePayment", back_populates="matches")
    
    def __repr__(self):
        return f"<StripeInvoiceMatch Payment {self.stripe_payment_id} - Invoice {self.whmcs_invoice_id}>"

class ApiLog(db.Model):
    """API request and error logging"""
    __tablename__ = 'api_logs'
    
    # Add extend_existing to avoid table definition conflicts
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    method = Column(String(10))  # GET, POST, PUT, DELETE, ERROR
    endpoint = Column(String(255))
    request_ip = Column(String(45))
    request_data = Column(Text)
    response_data = Column(Text)
    response_code = Column(Integer)
    execution_time = Column(Float)  # in milliseconds
    
    def __repr__(self):
        return f"<ApiLog {self.method} {self.endpoint} {self.response_code}>"
