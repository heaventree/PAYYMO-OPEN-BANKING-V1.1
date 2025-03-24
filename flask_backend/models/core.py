"""
Core models for the multi-tenant SaaS application
"""
import logging
from datetime import datetime
from enum import Enum
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    """Tenant status enum"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    TRIAL = 'trial'

class PlanType(Enum):
    """Subscription plan type enum"""
    FREE = 'free'
    STARTER = 'starter'
    PROFESSIONAL = 'professional'
    ENTERPRISE = 'enterprise'

class Tenant(db.Model):
    """Tenant model for multi-tenant SaaS application"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    domain = db.Column(db.String(255))
    status = db.Column(db.String(20), default=TenantStatus.TRIAL.value)
    plan = db.Column(db.String(20), default=PlanType.FREE.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Settings stored as JSON
    settings = db.Column(db.JSON)
    
    # Limits
    max_users = db.Column(db.Integer, default=2)
    max_integrations = db.Column(db.Integer, default=2)
    max_api_calls = db.Column(db.Integer, default=1000)
    
    # Billing information
    billing_email = db.Column(db.String(255))
    billing_name = db.Column(db.String(255))
    billing_address = db.Column(db.Text)
    billing_country = db.Column(db.String(2))
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_tenant_slug', slug),
        db.Index('idx_tenant_domain', domain),
        db.Index('idx_tenant_status', status),
    )
    
    def __repr__(self):
        return f'<Tenant {self.name} ({self.id})>'

class TenantQuota(db.Model):
    """Usage quota tracking for tenants"""
    __tablename__ = 'tenant_quotas'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    quota_type = db.Column(db.String(50), nullable=False)  # e.g., 'api_calls', 'storage', etc.
    limit = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Integer, default=0)
    reset_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tenant = db.relationship('Tenant', backref='quotas')
    
    # Add unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'quota_type', name='uq_tenant_quota_type'),
        db.Index('idx_tenant_quota_type', tenant_id, quota_type),
    )
    
    def __repr__(self):
        return f'<TenantQuota {self.quota_type} for Tenant {self.tenant_id}>'

class TenantUsageLog(db.Model):
    """Usage logging for tenant resources"""
    __tablename__ = 'tenant_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., 'api_call', 'storage', etc.
    quantity = db.Column(db.Integer, default=1)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    tenant = db.relationship('Tenant', backref='usage_logs')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_tenant_usage_resource', tenant_id, resource_type),
        db.Index('idx_tenant_usage_created', tenant_id, created_at),
    )
    
    def __repr__(self):
        return f'<TenantUsageLog {self.resource_type} ({self.quantity}) for Tenant {self.tenant_id}>'
