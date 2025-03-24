"""
Integration models for the multi-tenant SaaS application
"""
import logging
from datetime import datetime
from enum import Enum
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Integration type enum"""
    GOCARDLESS = 'gocardless'
    STRIPE = 'stripe'
    WHMCS = 'whmcs'
    WOOCOMMERCE = 'woocommerce'
    SHOPIFY = 'shopify'
    QUICKBOOKS = 'quickbooks'
    XERO = 'xero'
    CUSTOM = 'custom'

class IntegrationStatus(Enum):
    """Integration status enum"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ERROR = 'error'
    PENDING = 'pending'
    EXPIRED = 'expired'

class Integration(db.Model):
    """Integration model for external service connections"""
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default=IntegrationStatus.PENDING.value)
    config = db.Column(db.JSON)  # Configuration specific to this integration
    credentials = db.Column(db.JSON)  # Encrypted credentials
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = db.Column(db.DateTime)
    
    # Relationship
    tenant = db.relationship('Tenant', backref='integrations')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_integration_tenant', tenant_id),
        db.Index('idx_integration_type', type),
        db.Index('idx_integration_status', status),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Integration {self.name} ({self.type}) for Tenant {self.tenant_id}>'

class IntegrationSync(db.Model):
    """Integration sync history"""
    __tablename__ = 'integration_syncs'
    
    id = db.Column(db.Integer, primary_key=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'partial'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    # Relationships
    integration = db.relationship('Integration', backref='syncs')
    tenant = db.relationship('Tenant', backref='integration_syncs')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_sync_integration', integration_id),
        db.Index('idx_sync_tenant', tenant_id),
        db.Index('idx_sync_started', started_at),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<IntegrationSync {self.integration_id} ({self.status})>'

class Webhook(db.Model):
    """Webhooks for integration events"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'))
    url = db.Column(db.String(255), nullable=False)
    secret = db.Column(db.String(100))
    events = db.Column(db.JSON)  # List of events to trigger webhook
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='webhooks')
    integration = db.relationship('Integration', backref='webhooks')
    
    # Add indexes with unique names to avoid conflicts
    __table_args__ = (
        db.Index('idx_webhook_table_tenant', tenant_id),
        db.Index('idx_webhook_table_integration', integration_id),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<Webhook {self.url} for Tenant {self.tenant_id}>'

class WebhookEvent(db.Model):
    """Webhook event tracking"""
    __tablename__ = 'webhook_events'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhooks.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON)
    response_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    attempt_count = db.Column(db.Integer, default=1)
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempt_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    webhook = db.relationship('Webhook', backref='webhook_events')  # Changed backref name from 'events' to 'webhook_events'
    tenant = db.relationship('Tenant', backref='webhook_events')
    
    # Add indexes with unique names to avoid conflicts
    __table_args__ = (
        db.Index('idx_webhook_evt_webhook_id', webhook_id),
        db.Index('idx_webhook_evt_tenant_id', tenant_id),
        db.Index('idx_webhook_evt_event_type', event_type),
        db.Index('idx_webhook_evt_created_at', created_at),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<WebhookEvent {self.event_type} for Webhook {self.webhook_id}>'
