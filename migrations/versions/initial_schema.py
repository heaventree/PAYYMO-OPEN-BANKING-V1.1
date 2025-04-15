"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-04-15 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create license_keys table
    op.create_table(
        'license_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(64), unique=True, nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('owner_name', sa.String(255)),
        sa.Column('owner_email', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('last_verified', sa.DateTime()),
        sa.Column('allowed_domains', sa.Text()),
        sa.Column('max_banks', sa.Integer(), default=5),
        sa.Column('max_transactions', sa.Integer(), default=1000),
        sa.Column('features', sa.Text()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create whmcs_instances table
    op.create_table(
        'whmcs_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('license_key', sa.String(64), nullable=True),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('api_identifier', sa.String(255)),
        sa.Column('api_secret', sa.String(255)),
        sa.Column('admin_user', sa.String(100)),
        sa.Column('webhook_secret', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_seen', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bank_connections table
    op.create_table(
        'bank_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whmcs_instance_id', sa.Integer(), nullable=True),
        sa.Column('bank_id', sa.String(100), nullable=False),
        sa.Column('bank_name', sa.String(100)),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('account_name', sa.String(255)),
        sa.Column('access_token', sa.Text()),
        sa.Column('refresh_token', sa.Text()),
        sa.Column('token_expires_at', sa.DateTime()),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['whmcs_instance_id'], ['whmcs_instances.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create stripe_connections table
    op.create_table(
        'stripe_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whmcs_instance_id', sa.Integer(), nullable=True),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('account_name', sa.String(255)),
        sa.Column('account_email', sa.String(255)),
        sa.Column('access_token', sa.Text()),
        sa.Column('refresh_token', sa.Text()),
        sa.Column('token_expires_at', sa.DateTime()),
        sa.Column('publishable_key', sa.String(255)),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('account_type', sa.String(20), default='standard'),
        sa.Column('account_country', sa.String(2)),
        sa.ForeignKeyConstraint(['whmcs_instance_id'], ['whmcs_instances.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(100), unique=True, nullable=False),
        sa.Column('bank_id', sa.String(100)),
        sa.Column('bank_name', sa.String(100)),
        sa.Column('account_id', sa.String(100)),
        sa.Column('account_name', sa.String(255)),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), default='GBP'),
        sa.Column('description', sa.Text()),
        sa.Column('reference', sa.String(255)),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create stripe_payments table
    op.create_table(
        'stripe_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stripe_connection_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.String(100), unique=True, nullable=False),
        sa.Column('customer_id', sa.String(100)),
        sa.Column('customer_name', sa.String(255)),
        sa.Column('customer_email', sa.String(255)),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('description', sa.Text()),
        sa.Column('payment_metadata', sa.Text()),
        sa.Column('payment_date', sa.DateTime(), nullable=False),
        sa.Column('payment_status', sa.String(20), default='succeeded'),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['stripe_connection_id'], ['stripe_connections.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create invoice_matches table
    op.create_table(
        'invoice_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('whmcs_invoice_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('match_reason', sa.Text()),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create stripe_invoice_matches table
    op.create_table(
        'stripe_invoice_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stripe_payment_id', sa.Integer(), nullable=True),
        sa.Column('whmcs_invoice_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('match_reason', sa.Text()),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['stripe_payment_id'], ['stripe_payments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_license_keys_key', 'license_keys', ['key'])
    op.create_index('idx_whmcs_instances_domain', 'whmcs_instances', ['domain'])
    op.create_index('idx_whmcs_instances_license_key', 'whmcs_instances', ['license_key'])
    op.create_index('idx_bank_connections_bank_id', 'bank_connections', ['bank_id'])
    op.create_index('idx_bank_connections_whmcs_instance_id', 'bank_connections', ['whmcs_instance_id'])
    op.create_index('idx_stripe_connections_account_id', 'stripe_connections', ['account_id'])
    op.create_index('idx_stripe_connections_whmcs_instance_id', 'stripe_connections', ['whmcs_instance_id'])
    op.create_index('idx_transactions_transaction_id', 'transactions', ['transaction_id'])
    op.create_index('idx_transactions_transaction_date', 'transactions', ['transaction_date'])
    op.create_index('idx_stripe_payments_payment_id', 'stripe_payments', ['payment_id'])
    op.create_index('idx_stripe_payments_payment_date', 'stripe_payments', ['payment_date'])
    op.create_index('idx_invoice_matches_transaction_id', 'invoice_matches', ['transaction_id'])
    op.create_index('idx_invoice_matches_whmcs_invoice_id', 'invoice_matches', ['whmcs_invoice_id'])
    op.create_index('idx_stripe_invoice_matches_stripe_payment_id', 'stripe_invoice_matches', ['stripe_payment_id'])
    op.create_index('idx_stripe_invoice_matches_whmcs_invoice_id', 'stripe_invoice_matches', ['whmcs_invoice_id'])


def downgrade():
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('stripe_invoice_matches')
    op.drop_table('invoice_matches')
    op.drop_table('stripe_payments')
    op.drop_table('transactions')
    op.drop_table('stripe_connections')
    op.drop_table('bank_connections')
    op.drop_table('whmcs_instances')
    op.drop_table('license_keys')