"""
Financial data models for the multi-tenant SaaS application
"""
import logging
from datetime import datetime
from enum import Enum
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

class TransactionStatus(Enum):
    """Transaction status enum"""
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'

class InvoiceStatus(Enum):
    """Invoice status enum"""
    DRAFT = 'draft'
    OPEN = 'open'
    PAID = 'paid'
    OVERDUE = 'overdue'
    VOID = 'void'
    PARTIALLY_PAID = 'partially_paid'

class MatchStatus(Enum):
    """Match status enum for transaction-invoice matches"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    APPLIED = 'applied'

class StandardizedTransaction(db.Model):
    """Standardized transaction model across all payment sources"""
    __tablename__ = 'standardized_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'))
    source = db.Column(db.String(50), nullable=False)  # 'stripe', 'gocardless', etc.
    source_id = db.Column(db.String(100), nullable=False)  # ID from the original source
    amount = db.Column(db.Numeric(15, 6), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    reference = db.Column(db.String(255))
    transaction_date = db.Column(db.DateTime, nullable=False)
    transaction_metadata = db.Column(db.JSON)  # Additional data from source
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='transactions')
    integration = db.relationship('Integration', backref='transactions')
    
    # Add unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'source', 'source_id', name='uq_tenant_transaction_source'),
        db.Index('idx_transaction_tenant', tenant_id),
        db.Index('idx_transaction_source', source, source_id),
        db.Index('idx_transaction_date', transaction_date),
        db.Index('idx_transaction_status', status),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Transaction {self.source}:{self.source_id} {self.amount} {self.currency}>'

class StandardizedInvoice(db.Model):
    """Standardized invoice model across all invoice sources"""
    __tablename__ = 'standardized_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'))
    source = db.Column(db.String(50), nullable=False)  # 'whmcs', 'woocommerce', etc.
    source_id = db.Column(db.String(100), nullable=False)  # ID from the original source
    number = db.Column(db.String(100))  # Invoice number
    total = db.Column(db.Numeric(15, 6), nullable=False)
    balance = db.Column(db.Numeric(15, 6), nullable=False)  # Remaining balance
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    customer_id = db.Column(db.String(100))
    customer_name = db.Column(db.String(255))
    customer_email = db.Column(db.String(255))
    invoice_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime)
    invoice_metadata = db.Column(db.JSON)  # Additional data from source
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='invoices')
    integration = db.relationship('Integration', backref='invoices')
    
    # Add unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'source', 'source_id', name='uq_tenant_invoice_source'),
        db.Index('idx_invoice_tenant', tenant_id),
        db.Index('idx_invoice_source', source, source_id),
        db.Index('idx_invoice_date', invoice_date),
        db.Index('idx_invoice_status', status),
        db.Index('idx_invoice_customer', customer_id),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Invoice {self.source}:{self.source_id} {self.total} {self.currency}>'

class InvoiceTransaction(db.Model):
    """Matches between transactions and invoices"""
    __tablename__ = 'invoice_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('standardized_invoices.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('standardized_transactions.id'), nullable=False)
    amount_applied = db.Column(db.Numeric(15, 6), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), default=MatchStatus.PENDING.value)
    confidence = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    match_reason = db.Column(db.Text)
    confirmed_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='invoice_transactions')
    invoice = db.relationship('StandardizedInvoice', backref='transaction_matches')
    transaction = db.relationship('StandardizedTransaction', backref='invoice_matches')
    
    # Add unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('invoice_id', 'transaction_id', name='uq_invoice_transaction'),
        db.Index('idx_invoice_transaction_tenant', tenant_id),
        db.Index('idx_invoice_transaction_invoice', invoice_id),
        db.Index('idx_invoice_transaction_transaction', transaction_id),
        db.Index('idx_invoice_transaction_status', status),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<InvoiceTransaction Invoice {self.invoice_id} - Transaction {self.transaction_id}>'

class ReconciliationRule(db.Model):
    """Custom rules for transaction-invoice matching"""
    __tablename__ = 'reconciliation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    rule_type = db.Column(db.String(50), nullable=False)  # 'reference', 'amount', 'date', etc.
    rule_config = db.Column(db.JSON, nullable=False)  # Configuration specific to rule type
    priority = db.Column(db.Integer, default=100)  # Lower number = higher priority
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tenant = db.relationship('Tenant', backref='reconciliation_rules')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_rule_tenant', tenant_id),
        db.Index('idx_rule_type', rule_type),
        db.Index('idx_rule_active', is_active),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ReconciliationRule {self.name} ({self.rule_type}) for Tenant {self.tenant_id}>'
