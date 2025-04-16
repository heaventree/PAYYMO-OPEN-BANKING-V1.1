#!/usr/bin/env python3
"""
CI/CD Pipeline Migration Script

This script is designed to be used in CI/CD pipelines to safely
apply database migrations. It checks that migrations are safe to 
apply, applies them, and verifies the result.

Usage:
  python ci_migration.py 
  
Environment variables:
  DB_MIGRATION_LEVEL - Set to "check", "apply", or "verify"
  ALEMBIC_CONFIG - Path to the Alembic config file (default: alembic.ini)
  SKIP_TESTS - Set to "1" to skip migration tests
"""

import os
import sys
import subprocess
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ci_migration')


def run_command(command, capture_output=True, check=True):
    """Run a command and return the output"""
    try:
        logger.debug(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            check=check
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        if capture_output:
            logger.error(f"Error output: {e.stderr}")
        return False, str(e)


def check_migrations():
    """Check if migrations are needed and if they are safe to apply"""
    logger.info("Checking migrations...")
    
    # Check if there are pending migrations
    success, output = run_command(['python', 'manage.py', 'db', 'check'])
    
    if "Database is up to date" in output:
        logger.info("No migrations needed - database is up to date")
        return True, "No migrations needed"
    
    logger.info("Migrations needed")
    
    # Check if all migrations have tests
    if os.environ.get('SKIP_TESTS') != '1':
        logger.info("Testing migrations...")
        success, output = run_command(['python', 'test_migrations.py', '--latest'])
        
        if not success:
            logger.error("Migration tests failed")
            return False, "Migration tests failed"
    else:
        logger.warning("Skipping migration tests")
    
    return True, "Migrations ready to apply"


def apply_migrations():
    """Apply pending migrations"""
    logger.info("Applying migrations...")
    
    # Apply migrations using the db_upgrade.py script
    success, output = run_command(['python', 'db_upgrade.py', '--force'])
    
    if not success:
        logger.error(f"Failed to apply migrations: {output}")
        return False, "Failed to apply migrations"
    
    logger.info("Migrations applied successfully")
    return True, "Migrations applied successfully"


def verify_migrations():
    """Verify that migrations were applied correctly"""
    logger.info("Verifying migrations...")
    
    # Check if database is up to date
    success, output = run_command(['python', 'manage.py', 'db', 'check'])
    
    if "Database is up to date" not in output:
        logger.error("Database is not up to date after migrations")
        return False, "Database is not up to date after migrations"
    
    # Verify that the application can connect to the database
    try:
        # Import flask app and check database connection
        from flask_backend.app import app, db
        
        with app.app_context():
            # Try executing a simple query
            db.session.execute("SELECT 1")
            db.session.commit()
            
            logger.info("Database connection verified")
            return True, "Migrations verified successfully"
    except Exception as e:
        logger.error(f"Failed to verify database connection: {e}")
        return False, f"Failed to verify database connection: {e}"


def main():
    # Get migration level from environment variable
    migration_level = os.environ.get('DB_MIGRATION_LEVEL', 'check')
    
    if migration_level == 'check':
        success, message = check_migrations()
        if not success:
            logger.error(f"Migration check failed: {message}")
            sys.exit(1)
        
        logger.info(f"Migration check passed: {message}")
    
    elif migration_level == 'apply':
        # First check
        success, message = check_migrations()
        if not success:
            logger.error(f"Migration check failed: {message}")
            sys.exit(1)
        
        # Then apply
        success, message = apply_migrations()
        if not success:
            logger.error(f"Migration application failed: {message}")
            sys.exit(1)
        
        logger.info(f"Migrations applied: {message}")
    
    elif migration_level == 'verify':
        success, message = verify_migrations()
        if not success:
            logger.error(f"Migration verification failed: {message}")
            sys.exit(1)
        
        logger.info(f"Migration verification passed: {message}")
    
    elif migration_level == 'all':
        # Execute all steps
        success, message = check_migrations()
        if not success:
            logger.error(f"Migration check failed: {message}")
            sys.exit(1)
        
        success, message = apply_migrations()
        if not success:
            logger.error(f"Migration application failed: {message}")
            sys.exit(1)
        
        # Wait a moment to ensure database is ready
        time.sleep(2)
        
        success, message = verify_migrations()
        if not success:
            logger.error(f"Migration verification failed: {message}")
            sys.exit(1)
        
        logger.info("Migration process completed successfully")
    
    else:
        logger.error(f"Unknown migration level: {migration_level}")
        logger.error("Valid options: check, apply, verify, all")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()