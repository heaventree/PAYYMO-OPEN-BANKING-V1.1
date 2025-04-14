"""
Authentication models for the multi-tenant SaaS application
"""
import logging
from datetime import datetime
from enum import Enum
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role enum"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'
    API_USER = 'api_user'

class UserStatus(Enum):
    """User status enum"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'
    SUSPENDED = 'suspended'

class User(db.Model):
    """User model for multi-tenant SaaS application"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default=UserRole.USER.value)
    status = db.Column(db.String(20), default=UserStatus.PENDING.value)
    email_verified = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(255))
    verification_token = db.Column(db.String(255))
    preferences = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_user_email', email),
        db.Index('idx_user_status', status),
    )
    
    def __repr__(self):
        return f'<User {self.email} ({self.id})>'

class TenantUser(db.Model):
    """Association between users and tenants"""
    __tablename__ = 'tenant_users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default=UserRole.USER.value)
    is_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='users')
    user = db.relationship('User', backref='tenants')
    
    # Add unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),
        db.Index('idx_tenant_id', tenant_id),
        db.Index('idx_user_id', user_id),
    )
    
    def __repr__(self):
        return f'<TenantUser {self.tenant_id}:{self.user_id}>'

class LoginAttempt(db.Model):
    """Login attempt tracking"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    success = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    tenant = db.relationship('Tenant', backref='login_attempts')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_login_email', email),
        db.Index('idx_login_ip', ip_address),
        db.Index('idx_login_tenant', tenant_id),
    )
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} ({self.success})>'

class PasswordReset(db.Model):
    """Password reset tokens"""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='password_resets')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_reset_token', token),
        db.Index('idx_reset_user', user_id),
    )
    
    def __repr__(self):
        return f'<PasswordReset {self.user_id} ({self.token[:10]}...)>'

class ApiKey(db.Model):
    """API keys for tenant access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    key = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='api_keys')
    user = db.relationship('User', backref='api_keys')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_api_key', key),
        db.Index('idx_api_tenant', tenant_id),
        db.Index('idx_api_user', user_id),
    )
    
    def __repr__(self):
        return f'<ApiKey {self.name} ({self.key[:10]}...)>'

class ApiLog(db.Model):
    """API request logging"""
    __tablename__ = 'api_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    request_data = db.Column(db.Text)
    response_data = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # in milliseconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = db.relationship('ApiKey', backref='logs')
    tenant = db.relationship('Tenant', backref='api_logs')
    
    # Add indexes
    __table_args__ = (
        db.Index('idx_api_log_tenant', tenant_id),
        db.Index('idx_api_log_endpoint', endpoint),
        db.Index('idx_api_log_created', created_at),
    )
    
    def __repr__(self):
        return f'<ApiLog {self.endpoint} ({self.status_code})>'
