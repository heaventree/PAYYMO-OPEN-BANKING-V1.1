"""
Models package initialization
"""
from flask_backend.models.core import *
from flask_backend.models.auth import *
from flask_backend.models.integrations import *
from flask_backend.models.financial import *

# Import legacy models for backward compatibility
from flask_backend.legacy_models import (
    LicenseKey, WhmcsInstance, BankConnection, StripeConnection,
    Transaction, StripePayment, InvoiceMatch, StripeInvoiceMatch, ApiLog
)

# List of all models for documentation purposes
__all__ = [
    # Core models
    'Tenant', 'TenantStatus', 'PlanType', 'TenantQuota', 'TenantUsageLog',
    
    # Auth models
    'User', 'UserRole', 'UserStatus', 'TenantUser', 'LoginAttempt', 
    'PasswordReset', 'ApiKey', 'ApiLog',
    
    # Integration models
    'Integration', 'IntegrationType', 'IntegrationStatus', 'IntegrationSync',
    'Webhook', 'WebhookEvent',
    
    # Financial models
    'StandardizedTransaction', 'StandardizedInvoice', 'TransactionStatus',
    'InvoiceStatus', 'InvoiceTransaction', 'MatchStatus', 'ReconciliationRule',
    
    # Legacy models for compatibility
    'LicenseKey', 'WhmcsInstance', 'BankConnection', 'StripeConnection',
    'Transaction', 'StripePayment', 'InvoiceMatch', 'StripeInvoiceMatch'
]
