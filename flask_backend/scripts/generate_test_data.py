"""
Generate Test Data Script

This script generates test data for the multi-tenant SaaS application:
- Test tenant (if not exists)
- Sample integrations
- Sample transactions from various sources
- Sample invoices
- Sample matches between transactions and invoices

Run with: python -m flask_backend.scripts.generate_test_data
"""
import sys
import os
import random
import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask_backend.app import app, db
from flask_backend.models.auth import User, UserRole
from flask_backend.models.core import Tenant, TenantStatus, PlanType
from flask_backend.models.financial import (
    StandardizedTransaction, StandardizedInvoice, InvoiceTransaction,
    ReconciliationRule, TransactionStatus, InvoiceStatus, MatchStatus
)
from flask_backend.models.integrations import (
    Integration, IntegrationSync, Webhook, WebhookEvent,
    IntegrationType, IntegrationStatus
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_tenant():
    """Create a test tenant if it doesn't exist"""
    # Check if test tenant exists
    test_tenant = Tenant.query.filter_by(name='Test Company').first()
    
    if test_tenant:
        logger.info(f"Test tenant already exists: {test_tenant.name} (ID: {test_tenant.id})")
        return test_tenant
    
    # Create new test tenant
    test_tenant = Tenant(
        name='Test Company',
        slug='test-company',
        domain='test.example.com',
        status=TenantStatus.ACTIVE.value,
        plan_id=PlanType.PROFESSIONAL.value,
        settings={
            'timezone': 'America/New_York',
            'currency': 'USD',
            'contact_email': 'admin@test.com',
            'contact_phone': '+1234567890',
            'website': 'https://example.com',
            'address': '123 Test Street, Test City, 12345'
        }
    )
    
    db.session.add(test_tenant)
    db.session.commit()
    
    logger.info(f"Created test tenant: {test_tenant.name} (ID: {test_tenant.id})")
    
    # Create admin user for the tenant
    admin_user = User.query.filter_by(email='admin@test.com').first()
    
    if not admin_user:
        admin_user = User(
            tenant_id=test_tenant.id,
            name='Admin User',
            email='admin@test.com',
            password_hash='$2b$12$8M55ZaJ15n9y7AKuBCavreG51RyQ9lA1RcXUdugTuGW4aLPEFJ/oe',  # password123
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        logger.info(f"Created admin user for test tenant: {admin_user.email} (ID: {admin_user.id})")
    
    return test_tenant

def create_test_integrations(tenant_id):
    """Create test integrations for the tenant"""
    # Check if integrations already exist
    existing_integrations = Integration.query.filter_by(tenant_id=tenant_id).all()
    
    if existing_integrations:
        logger.info(f"Test tenant already has {len(existing_integrations)} integrations")
        return existing_integrations
    
    # Create sample integrations
    integrations = []
    
    # GoCardless integration
    gocardless_integration = Integration(
        tenant_id=tenant_id,
        type=IntegrationType.GOCARDLESS.value,
        name='Sample Bank Connection',
        status=IntegrationStatus.ACTIVE.value,
        config={
            'default_currency': 'GBP',
            'auto_sync': True,
            'sync_frequency': 'daily',
            'credentials': {
                'access_token': 'sample_access_token',
                'refresh_token': 'sample_refresh_token',
                'token_expires_at': (datetime.now() + timedelta(days=30)).isoformat()
            }
        },
        last_sync_at=datetime.now() - timedelta(hours=12)
    )
    db.session.add(gocardless_integration)
    
    # Stripe integration
    stripe_integration = Integration(
        tenant_id=tenant_id,
        type=IntegrationType.STRIPE.value,
        name='Sample Stripe Connection',
        status=IntegrationStatus.ACTIVE.value,
        config={
            'default_currency': 'USD',
            'auto_sync': True,
            'sync_frequency': 'daily',
            'credentials': {
                'account_id': 'acct_sample12345',
                'access_token': 'sample_stripe_token',
                'publishable_key': 'pk_test_sample'
            }
        },
        last_sync_at=datetime.now() - timedelta(hours=6)
    )
    db.session.add(stripe_integration)
    
    # WHMCS integration
    whmcs_integration = Integration(
        tenant_id=tenant_id,
        type=IntegrationType.WHMCS.value,
        name='Sample WHMCS Connection',
        status=IntegrationStatus.ACTIVE.value,
        config={
            'domain': 'whmcs.example.com',
            'auto_sync': True,
            'sync_frequency': 'hourly',
            'credentials': {
                'api_identifier': 'sample_api_identifier',
                'api_secret': 'sample_api_secret'
            }
        },
        last_sync_at=datetime.now() - timedelta(hours=1)
    )
    db.session.add(whmcs_integration)
    
    db.session.commit()
    
    integrations = [gocardless_integration, stripe_integration, whmcs_integration]
    logger.info(f"Created {len(integrations)} test integrations")
    
    # Create integration syncs
    for integration in integrations:
        for i in range(3):
            sync = IntegrationSync(
                integration_id=integration.id,
                tenant_id=tenant_id,
                status='success',
                started_at=datetime.now() - timedelta(days=i, hours=random.randint(1, 12)),
                completed_at=datetime.now() - timedelta(days=i, hours=random.randint(1, 12), minutes=random.randint(5, 30)),
                records_processed=random.randint(10, 100),
                records_created=random.randint(5, 50),
                records_updated=random.randint(0, 20),
                records_failed=random.randint(0, 5)
            )
            db.session.add(sync)
    
    db.session.commit()
    logger.info(f"Created integration sync history")
    
    return integrations

def create_test_transactions(tenant_id, integration_id, count=20):
    """Create test transactions for the tenant"""
    # Check if transactions already exist
    existing_transactions = StandardizedTransaction.query.filter_by(tenant_id=tenant_id).all()
    
    if existing_transactions:
        logger.info(f"Test tenant already has {len(existing_transactions)} transactions")
        return existing_transactions
    
    # Get the integration to determine the source type
    integration = Integration.query.get(integration_id)
    if not integration:
        logger.error(f"Integration not found: {integration_id}")
        return []
    
    source = integration.type
    
    # Create sample transactions
    transactions = []
    status_options = [status.value for status in TransactionStatus]
    
    for i in range(count):
        # Create a transaction date in the last 30 days
        days_ago = random.randint(0, 30)
        transaction_date = datetime.now() - timedelta(days=days_ago)
        
        # Randomize amount between $10 and $1000
        amount = round(random.uniform(10, 1000), 2)
        
        # Set currency based on integration type
        currency = 'GBP' if source == IntegrationType.GOCARDLESS.value else 'USD'
        
        # Generate a unique source ID
        source_id = f"{source}-{tenant_id}-{i+1}"
        
        # Create the transaction
        transaction = StandardizedTransaction(
            tenant_id=tenant_id,
            integration_id=integration_id,
            source=source,
            source_id=source_id,
            amount=amount,
            currency=currency,
            status=random.choice(status_options),
            description=f"Sample transaction {i+1} from {source}",
            reference=f"REF-{i+1}-{random.randint(1000, 9999)}",
            transaction_date=transaction_date,
            transaction_type='payment',
            payment_method='bank_transfer' if source == IntegrationType.GOCARDLESS.value else 'card',
            transaction_metadata={
                'source_system': source,
                'customer_reference': f"CUST-{random.randint(1000, 9999)}",
                'processing_fee': round(amount * 0.03, 2) if source == IntegrationType.STRIPE.value else 0
            }
        )
        
        db.session.add(transaction)
        transactions.append(transaction)
    
    db.session.commit()
    
    logger.info(f"Created {len(transactions)} test transactions from {source}")
    return transactions

def create_test_invoices(tenant_id, integration_id, count=15):
    """Create test invoices for the tenant"""
    # Check if invoices already exist
    existing_invoices = StandardizedInvoice.query.filter_by(tenant_id=tenant_id).all()
    
    if existing_invoices:
        logger.info(f"Test tenant already has {len(existing_invoices)} invoices")
        return existing_invoices
    
    # Get the integration to determine the source type
    integration = Integration.query.get(integration_id)
    if not integration:
        logger.error(f"Integration not found: {integration_id}")
        return []
    
    source = integration.type
    
    # Create sample invoices
    invoices = []
    status_options = [status.value for status in InvoiceStatus]
    
    for i in range(count):
        # Create an invoice date in the last 30 days
        days_ago = random.randint(0, 30)
        invoice_date = datetime.now() - timedelta(days=days_ago)
        
        # Due date is typically 15 or 30 days after invoice date
        due_date = invoice_date + timedelta(days=random.choice([15, 30]))
        
        # Randomize amount between $50 and $2000
        total = round(random.uniform(50, 2000), 2)
        
        # Set a random balance based on total (could be fully paid or partially paid)
        payment_status = random.choice(['paid', 'partial', 'unpaid'])
        
        if payment_status == 'paid':
            balance = 0
            status = InvoiceStatus.PAID.value
        elif payment_status == 'partial':
            balance = round(total * random.uniform(0.3, 0.9), 2)
            status = InvoiceStatus.PARTIALLY_PAID.value
        else:
            balance = total
            status = random.choice([InvoiceStatus.OPEN.value, InvoiceStatus.OVERDUE.value])
        
        # Set currency based on integration type
        currency = 'USD'  # Most WHMCS instances use USD
        
        # Generate a unique source ID and invoice number
        source_id = f"{source}-{tenant_id}-{i+1}"
        invoice_number = f"INV-{datetime.now().year}-{i+1:04d}"
        
        # Create customer information
        customer_id = f"CUST-{random.randint(1000, 9999)}"
        customer_name = f"Test Customer {i+1}"
        customer_email = f"customer{i+1}@example.com"
        
        # Create the invoice
        invoice = StandardizedInvoice(
            tenant_id=tenant_id,
            integration_id=integration_id,
            source=source,
            source_id=source_id,
            number=invoice_number,
            total=total,
            balance=balance,
            currency=currency,
            status=status,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            invoice_date=invoice_date,
            due_date=due_date,
            invoice_metadata={
                'source_system': source,
                'items': [
                    {
                        'description': 'Web Hosting Plan',
                        'amount': round(total * 0.7, 2),
                        'quantity': 1
                    },
                    {
                        'description': 'Domain Registration',
                        'amount': round(total * 0.3, 2),
                        'quantity': 1
                    }
                ]
            }
        )
        
        db.session.add(invoice)
        invoices.append(invoice)
    
    db.session.commit()
    
    logger.info(f"Created {len(invoices)} test invoices from {source}")
    return invoices

def create_test_matches(tenant_id, transactions, invoices, count=10):
    """Create test matches between transactions and invoices"""
    # Check if matches already exist
    existing_matches = InvoiceTransaction.query.filter_by(tenant_id=tenant_id).all()
    
    if existing_matches:
        logger.info(f"Test tenant already has {len(existing_matches)} transaction-invoice matches")
        return existing_matches
    
    # Create sample matches
    matches = []
    status_options = [status.value for status in MatchStatus]
    
    # Only use transactions and invoices with matching currencies
    valid_transactions = transactions.copy()
    valid_invoices = [inv for inv in invoices if inv.balance > 0]
    
    if not valid_transactions or not valid_invoices:
        logger.warning("No valid transactions or invoices to create matches")
        return []
    
    # Create matches (up to the count or available transactions/invoices)
    match_count = min(count, len(valid_transactions), len(valid_invoices))
    
    for i in range(match_count):
        transaction = valid_transactions[i]
        invoice = valid_invoices[i]
        
        # Determine amount applied (either full transaction or partial)
        if random.choice([True, False]) and transaction.amount <= invoice.balance:
            amount_applied = transaction.amount
        else:
            amount_applied = min(transaction.amount, invoice.balance)
        
        # Select a match status
        status = random.choice(status_options)
        
        # Set confidence level based on status
        if status == MatchStatus.APPROVED.value:
            confidence = random.uniform(0.8, 1.0)
        elif status == MatchStatus.PENDING.value:
            confidence = random.uniform(0.5, 0.8)
        else:
            confidence = random.uniform(0.1, 0.5)
        
        # Create reason based on confidence
        if confidence > 0.8:
            reason = "High confidence match: Exact amount and reference match"
        elif confidence > 0.5:
            reason = "Medium confidence match: Amount match but no reference match"
        else:
            reason = "Low confidence match: Partial amount match"
        
        # Create the match
        match = InvoiceTransaction(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            transaction_id=transaction.id,
            amount_applied=amount_applied,
            currency=transaction.currency,
            status=status,
            confidence=confidence,
            match_reason=reason,
            applied_at=datetime.now() if status == MatchStatus.APPROVED.value else None
        )
        
        db.session.add(match)
        matches.append(match)
    
    db.session.commit()
    
    logger.info(f"Created {len(matches)} test transaction-invoice matches")
    return matches

def create_test_reconciliation_rules(tenant_id):
    """Create test reconciliation rules for the tenant"""
    # Check if rules already exist
    existing_rules = ReconciliationRule.query.filter_by(tenant_id=tenant_id).all()
    
    if existing_rules:
        logger.info(f"Test tenant already has {len(existing_rules)} reconciliation rules")
        return existing_rules
    
    # Create sample rules
    rules = []
    
    # Rule 1: Match by invoice number in reference
    rule1 = ReconciliationRule(
        tenant_id=tenant_id,
        name="Invoice Number in Reference",
        description="Match transactions with invoice number in the reference field",
        rule_type="reference",
        rule_config={
            "pattern": "INV-\\d{4}-\\d{4}",
            "field": "reference",
            "extract_pattern": "INV-\\d{4}-\\d{4}",
            "weight": 0.7
        },
        priority=10,
        is_active=True
    )
    db.session.add(rule1)
    rules.append(rule1)
    
    # Rule 2: Exact amount match
    rule2 = ReconciliationRule(
        tenant_id=tenant_id,
        name="Exact Amount Match",
        description="Match transactions with exactly the same amount as the invoice",
        rule_type="amount",
        rule_config={
            "tolerance": 0.01,
            "match_type": "exact",
            "weight": 0.5
        },
        priority=20,
        is_active=True
    )
    db.session.add(rule2)
    rules.append(rule2)
    
    # Rule 3: Customer name in description
    rule3 = ReconciliationRule(
        tenant_id=tenant_id,
        name="Customer Name in Description",
        description="Match transactions that contain the customer name in the description",
        rule_type="description",
        rule_config={
            "field": "description",
            "match_type": "contains",
            "weight": 0.3
        },
        priority=30,
        is_active=True
    )
    db.session.add(rule3)
    rules.append(rule3)
    
    # Rule 4: Date proximity
    rule4 = ReconciliationRule(
        tenant_id=tenant_id,
        name="Date Proximity",
        description="Match transactions that are within 5 days of the invoice date",
        rule_type="date",
        rule_config={
            "max_days": 5,
            "weight": 0.2
        },
        priority=40,
        is_active=True
    )
    db.session.add(rule4)
    rules.append(rule4)
    
    db.session.commit()
    
    logger.info(f"Created {len(rules)} test reconciliation rules")
    return rules

def main():
    """Main function to generate test data"""
    with app.app_context():
        logger.info("Starting test data generation")
        
        # Create test tenant
        tenant = create_test_tenant()
        
        # Create test integrations
        integrations = create_test_integrations(tenant.id)
        
        # Create test transactions for each integration type
        all_transactions = []
        for integration in integrations:
            if integration.type == IntegrationType.GOCARDLESS.value:
                transactions = create_test_transactions(tenant.id, integration.id, count=20)
                all_transactions.extend(transactions)
            elif integration.type == IntegrationType.STRIPE.value:
                transactions = create_test_transactions(tenant.id, integration.id, count=15)
                all_transactions.extend(transactions)
        
        # Create test invoices for the WHMCS integration
        whmcs_integration = next((i for i in integrations if i.type == IntegrationType.WHMCS.value), None)
        if whmcs_integration:
            invoices = create_test_invoices(tenant.id, whmcs_integration.id, count=15)
        else:
            logger.error("WHMCS integration not found, skipping invoice creation")
            invoices = []
        
        # Create test matches between transactions and invoices
        if all_transactions and invoices:
            matches = create_test_matches(tenant.id, all_transactions, invoices, count=10)
        else:
            logger.warning("No transactions or invoices available, skipping match creation")
        
        # Create test reconciliation rules
        rules = create_test_reconciliation_rules(tenant.id)
        
        logger.info("Test data generation completed successfully")

if __name__ == "__main__":
    main()