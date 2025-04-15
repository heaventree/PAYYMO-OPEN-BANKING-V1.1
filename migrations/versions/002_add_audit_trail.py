"""Add audit trail table for tracking changes

Revision ID: 002_add_audit_trail
Revises: 001_initial_schema
Create Date: 2025-04-15 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_audit_trail'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create database_audit_trail table to track changes
    op.create_table(
        'database_audit_trail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),  # INSERT, UPDATE, DELETE
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('whmcs_instance_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('old_values', sa.Text(), nullable=True),  # JSON string of old values
        sa.Column('new_values', sa.Text(), nullable=True),  # JSON string of new values
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('additional_context', sa.Text(), nullable=True),  # For any other relevant info
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better querying performance
    op.create_index('idx_audit_trail_table', 'database_audit_trail', ['table_name'])
    op.create_index('idx_audit_trail_operation', 'database_audit_trail', ['operation'])
    op.create_index('idx_audit_trail_timestamp', 'database_audit_trail', ['timestamp'])
    op.create_index('idx_audit_trail_whmcs_instance', 'database_audit_trail', ['whmcs_instance_id'])
    op.create_index('idx_audit_trail_user', 'database_audit_trail', ['user_id'])

    # Create foreign key connection to whmcs_instances
    op.create_foreign_key(
        'fk_audit_trail_whmcs_instance',
        'database_audit_trail', 'whmcs_instances',
        ['whmcs_instance_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add tracking columns to all major tables
    for table in ['license_keys', 'whmcs_instances', 'bank_connections', 'stripe_connections', 
                  'transactions', 'stripe_payments', 'invoice_matches', 'stripe_invoice_matches']:
        op.add_column(table, sa.Column('last_modified_by', sa.Integer(), nullable=True))
        op.add_column(table, sa.Column('last_modified_at', sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    # Drop tracking columns from all tables (reverse order)
    for table in ['stripe_invoice_matches', 'invoice_matches', 'stripe_payments', 'transactions',
                  'stripe_connections', 'bank_connections', 'whmcs_instances', 'license_keys']:
        op.drop_column(table, 'is_deleted')
        op.drop_column(table, 'last_modified_at')
        op.drop_column(table, 'last_modified_by')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_audit_trail_whmcs_instance', 'database_audit_trail', type_='foreignkey')
    
    # Drop the audit trail table
    op.drop_table('database_audit_trail')