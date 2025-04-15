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
    # Check if tables already exist (since we're using the existing database)
    from sqlalchemy import inspect
    from sqlalchemy.exc import OperationalError
    
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # Create database_audit_trail table to track changes if it doesn't exist
    if 'database_audit_trail' not in existing_tables:
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
        
        # Create indexes for better querying performance - only if we created the table
        try:
            op.create_index('idx_audit_trail_table', 'database_audit_trail', ['table_name'])
            op.create_index('idx_audit_trail_operation', 'database_audit_trail', ['operation'])
            op.create_index('idx_audit_trail_timestamp', 'database_audit_trail', ['timestamp'])
            op.create_index('idx_audit_trail_whmcs_instance', 'database_audit_trail', ['whmcs_instance_id'])
            op.create_index('idx_audit_trail_user', 'database_audit_trail', ['user_id'])

            # Create foreign key connection to whmcs_instances if it exists
            if 'whmcs_instances' in existing_tables:
                op.create_foreign_key(
                    'fk_audit_trail_whmcs_instance',
                    'database_audit_trail', 'whmcs_instances',
                    ['whmcs_instance_id'], ['id'],
                    ondelete='SET NULL'
                )
        except Exception as e:
            print(f"Warning: Error creating indexes or foreign keys: {str(e)}")
    
    # Add tracking columns to all major tables that exist
    for table in ['license_keys', 'whmcs_instances', 'bank_connections', 'stripe_connections', 
                  'transactions', 'stripe_payments', 'invoice_matches', 'stripe_invoice_matches']:
        if table in existing_tables:
            # Check if columns already exist (they might have been added manually)
            columns = [col['name'] for col in inspector.get_columns(table)]
            try:
                if 'last_modified_by' not in columns:
                    op.add_column(table, sa.Column('last_modified_by', sa.Integer(), nullable=True))
                if 'last_modified_at' not in columns:    
                    op.add_column(table, sa.Column('last_modified_at', sa.DateTime(), nullable=True))
                if 'is_deleted' not in columns:
                    op.add_column(table, sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
            except Exception as e:
                print(f"Warning: Error adding tracking columns to {table}: {str(e)}")


def downgrade():
    # Check if tables and columns exist before trying to drop them
    from sqlalchemy import inspect
    from sqlalchemy.exc import OperationalError
    
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # Drop tracking columns from all tables (reverse order)
    for table in ['stripe_invoice_matches', 'invoice_matches', 'stripe_payments', 'transactions',
                  'stripe_connections', 'bank_connections', 'whmcs_instances', 'license_keys']:
        if table in existing_tables:
            columns = [col['name'] for col in inspector.get_columns(table)]
            try:
                if 'is_deleted' in columns:
                    op.drop_column(table, 'is_deleted')
                if 'last_modified_at' in columns:
                    op.drop_column(table, 'last_modified_at')
                if 'last_modified_by' in columns:
                    op.drop_column(table, 'last_modified_by')
            except Exception as e:
                print(f"Warning: Error dropping columns from {table}: {str(e)}")
    
    # Only drop the constraint and table if they exist
    if 'database_audit_trail' in existing_tables:
        try:
            # Check if foreign key exists before dropping
            foreign_keys = inspector.get_foreign_keys('database_audit_trail')
            fk_names = [fk['name'] for fk in foreign_keys]
            if 'fk_audit_trail_whmcs_instance' in fk_names:
                op.drop_constraint('fk_audit_trail_whmcs_instance', 'database_audit_trail', type_='foreignkey')
            
            # Drop the audit trail table
            op.drop_table('database_audit_trail')
        except Exception as e:
            print(f"Warning: Error dropping database_audit_trail table: {str(e)}")