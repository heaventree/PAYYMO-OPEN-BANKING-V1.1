#!/usr/bin/env python3
"""
Safe Database Upgrade Script

This script safely applies database migrations and performs necessary checks
to ensure the database is in a consistent state before and after migrations.

It uses the migration utilities from flask_backend.utils.migrations to perform
database checks, create backups, and verify integrity before and after migrations.

Usage:
  python db_upgrade.py                   # Apply all pending migrations
  python db_upgrade.py --check-only      # Only check if migrations are needed
  python db_upgrade.py --backup          # Create a backup before migrating
  python db_upgrade.py --force           # Skip confirmation prompt
  python db_upgrade.py --verify          # Perform database integrity verification
"""

import os
import sys
import argparse
import subprocess
import datetime
import logging

# Import our custom migration utilities
from flask_backend.utils.migrations import (
    check_database_connection, create_table_backup, verify_database_integrity,
    get_logger, get_database_url, get_database_engine
)

# Configure logging
logger = get_logger('db_upgrade')


def run_command(command):
    """Run a command and return the output"""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Command failed with error: {e.stderr}"


def create_database_backup():
    """Create a backup of the database by backing up all tables"""
    try:
        # Get current timestamp for backup naming
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get database tables
        from flask_backend.utils.migrations import list_tables, create_table_backup
        
        tables = list_tables()
        if not tables:
            logger.error("No tables found in database")
            return False, None
        
        # Create backup directory
        backup_dir = f"backups/db_backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup of each table
        backup_tables = []
        for table in tables:
            # Skip alembic version table
            if table == 'alembic_version':
                continue
                
            backup_table = create_table_backup(table, timestamp)
            if backup_table:
                backup_tables.append(backup_table)
        
        if not backup_tables:
            logger.error("Failed to create any table backups")
            return False, None
            
        logger.info(f"Created backup of {len(backup_tables)} tables")
        return True, backup_dir
        
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        return False, None


def check_pending_migrations():
    """Check if there are pending migrations to apply"""
    success, output = run_command(['python', 'manage.py', 'db', 'check'])
    if "Database is up to date" in output:
        return False  # No pending migrations
    return True  # Pending migrations exist


def apply_migrations():
    """Apply all pending database migrations"""
    logger.info("Applying database migrations...")
    success, output = run_command(['python', 'manage.py', 'db', 'upgrade'])
    
    if success:
        logger.info("Database migrations applied successfully")
        return True
    else:
        logger.error(f"Failed to apply migrations: {output}")
        return False


def verify_database_integrity():
    """Verify database integrity after migration"""
    from flask_backend.utils.migrations import verify_database_integrity as check_integrity
    
    try:
        # Use the utility function to perform standard integrity checks
        results = check_integrity()
        
        if not results['success']:
            for issue in results['issues']:
                logger.error(f"Database integrity check failed: {issue}")
            return False
            
        # Additional application-specific checks
        # Perform deeper validation beyond table existence
        tables = results['tables']
        
        # Check for specific columns in critical tables
        if 'license_keys' in tables:
            from flask_backend.utils.migrations import column_exists
            required_columns = [
                ('license_keys', 'key'),
                ('license_keys', 'status'),
                ('license_keys', 'owner_email'),
                ('license_keys', 'expires_at'),
                ('whmcs_instances', 'domain'),
                ('whmcs_instances', 'license_key'),
                ('transactions', 'transaction_id'),
                ('transactions', 'amount'),
                ('transactions', 'transaction_date')
            ]
            
            for table, column in required_columns:
                if table in tables and not column_exists(table, column):
                    logger.error(f"Database integrity check failed: Missing column {column} in table {table}")
                    return False
        
        # Check for tracking columns added by migrations
        tracking_columns = [
            ('license_keys', 'last_modified_at'),
            ('license_keys', 'last_modified_by'),
            ('license_keys', 'is_deleted'),
            ('whmcs_instances', 'last_modified_at'),
            ('whmcs_instances', 'last_modified_by'),
            ('whmcs_instances', 'is_deleted')
        ]
        
        for table, column in tracking_columns:
            if table in tables and not column_exists(table, column):
                logger.warning(f"Missing tracking column {column} in table {table}")
                # Don't fail for missing tracking columns, just warn
        
        # Check for audit trail table
        if 'database_audit_trail' not in tables:
            logger.error("Database integrity check failed: Missing audit trail table")
            return False
                
        logger.info("Database integrity check passed")
        return True
    except Exception as e:
        logger.error(f"Database integrity check failed with error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Safe database upgrade tool')
    parser.add_argument('--check-only', action='store_true', help='Only check if migrations are needed')
    parser.add_argument('--backup', action='store_true', help='Create a backup before migrating')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Check database connection
    logger.info("Checking database connection...")
    if not check_database_connection():
        logger.error("Cannot connect to database, aborting")
        sys.exit(1)
    
    # Check if migrations are pending
    pending = check_pending_migrations()
    if not pending:
        logger.info("No database migrations pending")
        sys.exit(0)
    
    if args.check_only:
        logger.info("Database migrations are needed")
        sys.exit(0)
    
    # Create backup if requested
    if args.backup:
        logger.info("Creating database backup...")
        backup_success, backup_file = create_database_backup()
        if not backup_success:
            if not args.force:
                logger.error("Database backup failed and --force was not specified, aborting")
                sys.exit(1)
            else:
                logger.warning("Database backup failed, but continuing due to --force flag")
    
    # Confirm before proceeding
    if not args.force:
        confirm = input("Ready to apply database migrations. Continue? [y/N] ").lower()
        if confirm != 'y':
            logger.info("Migration cancelled by user")
            sys.exit(0)
    
    # Apply migrations
    if not apply_migrations():
        logger.error("Migration failed, check logs for details")
        sys.exit(1)
    
    # Verify database integrity
    if not verify_database_integrity():
        logger.error("Database integrity check failed after migration")
        # In a production system, you might want to restore from backup here
        sys.exit(1)
    
    logger.info("Database upgrade completed successfully")


if __name__ == '__main__':
    main()