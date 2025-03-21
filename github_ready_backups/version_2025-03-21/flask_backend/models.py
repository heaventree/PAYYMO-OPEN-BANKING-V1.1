from datetime import datetime
from flask_backend.app import db
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

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

class LicenseVerification(db.Model):
    """Log of license verification attempts"""
    __tablename__ = 'license_verifications'
    
    id = Column(Integer, primary_key=True)
    license_key = Column(String(64), nullable=False)
    verified_at = Column(DateTime, default=datetime.utcnow)
    domain = Column(String(255))
    ip_address = Column(String(45))
    success = Column(Boolean, default=False)
    message = Column(Text)
    
    def __repr__(self):
        return f"<LicenseVerification {self.license_key} at {self.verified_at}>"

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
    
    # Indices for faster queries
    __table_args__ = (
        Index('idx_transaction_id', transaction_id),
        Index('idx_bank_id', bank_id),
        Index('idx_account_id', account_id),
        Index('idx_transaction_date', transaction_date),
    )
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id} {self.amount} {self.currency}>"

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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to transaction
    transaction = relationship("Transaction", backref="matches")
    
    __table_args__ = (
        Index('idx_transaction_invoice', transaction_id, whmcs_invoice_id, unique=True),
        Index('idx_status', status),
    )
    
    def __repr__(self):
        return f"<InvoiceMatch Transaction {self.transaction_id} -> Invoice {self.whmcs_invoice_id}>"

class WhmcsInstance(db.Model):
    """Details of connected WHMCS instances"""
    __tablename__ = 'whmcs_instances'
    
    id = Column(Integer, primary_key=True)
    license_key = Column(String(64), ForeignKey('license_keys.key'))
    domain = Column(String(255), nullable=False)
    api_identifier = Column(String(255))
    api_secret = Column(String(255))
    admin_user = Column(String(100))
    webhook_secret = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to WHMCS instance
    whmcs_instance = relationship("WhmcsInstance", backref="bank_connections")
    
    def __repr__(self):
        return f"<BankConnection {self.bank_name} - {self.account_name}>"

class ApiLog(db.Model):
    """Log of API requests and responses"""
    __tablename__ = 'api_logs'
    
    id = Column(Integer, primary_key=True)
    endpoint = Column(String(255))
    method = Column(String(10))
    request_data = Column(Text)
    response_data = Column(Text)
    status_code = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    duration_ms = Column(Integer)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ApiLog {self.endpoint} {self.method} {self.status_code}>"
