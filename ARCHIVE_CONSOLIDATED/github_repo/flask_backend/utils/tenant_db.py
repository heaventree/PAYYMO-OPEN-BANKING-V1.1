"""
Tenant database utilities for the multi-tenant SaaS application
Implements schema-based tenant isolation in PostgreSQL
"""
import logging
from flask import g, current_app
from sqlalchemy import text
from flask_backend.app import db

# Setup logging
logger = logging.getLogger(__name__)

def create_tenant_schema(tenant_id):
    """
    Create a new schema for a tenant
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        True if successful, False otherwise
    """
    schema_name = f"tenant_{tenant_id}"
    
    try:
        # Create schema
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        db.session.commit()
        logger.info(f"Created schema {schema_name} for tenant {tenant_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating schema for tenant {tenant_id}: {str(e)}")
        return False

def drop_tenant_schema(tenant_id):
    """
    Drop a tenant schema and all its objects
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        True if successful, False otherwise
    """
    schema_name = f"tenant_{tenant_id}"
    
    try:
        # Drop schema with cascade
        db.session.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        db.session.commit()
        logger.info(f"Dropped schema {schema_name} for tenant {tenant_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error dropping schema for tenant {tenant_id}: {str(e)}")
        return False

def set_tenant_search_path(tenant_id=None):
    """
    Set search_path for the current database session to include tenant schema
    
    Args:
        tenant_id: The tenant ID, or None to use the tenant from the request context
        
    Returns:
        True if successful, False otherwise
    """
    # If no tenant_id provided, try to get from request context
    if tenant_id is None:
        tenant_id = getattr(g, 'tenant_id', None)
        
    if tenant_id is None:
        # No tenant context, use public schema only
        search_path = 'public'
    else:
        # Include tenant schema in search path
        search_path = f'tenant_{tenant_id}, public'
        
    try:
        # Set search_path for current connection
        db.session.execute(text(f'SET search_path TO {search_path}'))
        logger.debug(f"Set search_path to: {search_path}")
        return True
    except Exception as e:
        logger.error(f"Error setting search_path: {str(e)}")
        return False

def get_tenant_table_sizes(tenant_id):
    """
    Get size information for a tenant's tables
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        Dictionary of table sizes in bytes
    """
    schema_name = f"tenant_{tenant_id}"
    
    try:
        query = text(f"""
            SELECT 
                table_name,
                pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') AS total_bytes,
                pg_relation_size('"' || table_schema || '"."' || table_name || '"') AS table_bytes,
                pg_indexes_size('"' || table_schema || '"."' || table_name || '"') AS index_bytes,
                pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') - 
                    pg_relation_size('"' || table_schema || '"."' || table_name || '"') - 
                    pg_indexes_size('"' || table_schema || '"."' || table_name || '"') AS toast_bytes
            FROM information_schema.tables
            WHERE table_schema = :schema_name
            AND table_type = 'BASE TABLE'
            ORDER BY total_bytes DESC
        """)
        
        result = db.session.execute(query, {'schema_name': schema_name})
        
        sizes = {}
        for row in result:
            sizes[row[0]] = {
                'total_bytes': row[1],
                'table_bytes': row[2],
                'index_bytes': row[3],
                'toast_bytes': row[4]
            }
            
        return sizes
    except Exception as e:
        logger.error(f"Error getting table sizes for tenant {tenant_id}: {str(e)}")
        return {}

def get_tenant_row_counts(tenant_id):
    """
    Get row counts for a tenant's tables
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        Dictionary of table row counts
    """
    schema_name = f"tenant_{tenant_id}"
    
    try:
        # First get a list of tables in the schema
        tables_query = text(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
            AND table_type = 'BASE TABLE'
        """)
        
        tables = db.session.execute(tables_query, {'schema_name': schema_name}).fetchall()
        
        # Then get row counts for each table
        row_counts = {}
        for table in tables:
            table_name = table[0]
            count_query = text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
            count = db.session.execute(count_query).scalar()
            row_counts[table_name] = count
            
        return row_counts
    except Exception as e:
        logger.error(f"Error getting row counts for tenant {tenant_id}: {str(e)}")
        return {}

def migrate_tenant_schema(tenant_id):
    """
    Apply migrations to a tenant schema
    
    This function should be called after creating a new tenant schema
    or when updating the application schema
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        True if successful, False otherwise
    """
    schema_name = f"tenant_{tenant_id}"
    
    try:
        # First ensure schema exists
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        
        # Set search path to tenant schema
        db.session.execute(text(f'SET search_path TO {schema_name}, public'))
        
        # TODO: Apply migrations specific to tenant schema
        # This would typically use Flask-Migrate or Alembic to apply migrations
        
        db.session.commit()
        logger.info(f"Migrated schema {schema_name} for tenant {tenant_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error migrating schema for tenant {tenant_id}: {str(e)}")
        return False
