#!/usr/bin/env python3
"""
Safe Database Upgrade Script

This script safely applies database migrations and performs necessary checks
to ensure the database is in a consistent state before and after migrations.

Usage:
  python db_upgrade.py                   # Apply all pending migrations
  python db_upgrade.py --check-only      # Only check if migrations are needed
  python db_upgrade.py --backup          # Create a backup before migrating
  python db_upgrade.py --force           # Skip confirmation prompt
"""

import os
import sys
import argparse
import subprocess
import datetime
import logging
from flask_backend.app import app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_upgrade')


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


def check_database_connection():
    """Check if database is accessible"""
    try:
        with app.app_context():
            # Try executing a simple query
            db.session.execute("SELECT 1")
            db.session.commit()
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def create_database_backup():
    """Create a backup of the database"""
    # This is a placeholder - implement actual database backup logic
    # based on your database type (PostgreSQL, MySQL, etc.)
    backup_filename = f"db_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    logger.info(f"Creating database backup: {backup_filename}")
    
    # Example for PostgreSQL (adjust according to your DB)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if db_url.startswith('postgresql'):
        # Parse connection details
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        dbname = parsed.path[1:]  # Remove leading slash
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', str(port),
            '-U', user,
            '-F', 'c',  # Custom format (compressed)
            '-f', f"backups/{backup_filename}",
            dbname
        ]
        
        # Ensure backups directory exists
        os.makedirs('backups', exist_ok=True)
        
        # Execute backup command
        success, output = run_command(cmd)
        if success:
            logger.info("Database backup completed successfully")
            return True, backup_filename
        else:
            logger.error(f"Database backup failed: {output}")
            return False, None
    else:
        logger.warning("Database backup is only supported for PostgreSQL currently")
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
    # This function would contain checks specific to your application
    # to ensure the database is in a valid state after migrations
    
    try:
        with app.app_context():
            # Example check: Verify that all expected tables exist
            table_names = db.engine.table_names()
            expected_tables = [
                'license_keys', 'whmcs_instances', 'bank_connections',
                'stripe_connections', 'transactions', 'stripe_payments',
                'invoice_matches', 'stripe_invoice_matches'
            ]
            
            missing_tables = [t for t in expected_tables if t not in table_names]
            if missing_tables:
                logger.error(f"Database integrity check failed: Missing tables: {missing_tables}")
                return False
                
            logger.info("Database integrity check passed")
            return True
    except Exception as e:
        logger.error(f"Database integrity check failed with error: {e}")
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