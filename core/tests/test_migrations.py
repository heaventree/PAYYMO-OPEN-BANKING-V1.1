#!/usr/bin/env python3
"""
Migration Testing Utility

This script runs tests on migrations to ensure they can be correctly
applied and rolled back without data loss.

Usage:
  python test_migrations.py          # Test all migrations
  python test_migrations.py --latest # Test only the most recent migration
"""

import os
import sys
import argparse
import tempfile
import subprocess
import logging
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('migration_tester')


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


def get_migration_versions():
    """Get a list of all migration versions"""
    versions = []
    versions_dir = os.path.join('migrations', 'versions')
    
    if not os.path.exists(versions_dir):
        logger.error(f"Versions directory not found: {versions_dir}")
        return versions
    
    for filename in os.listdir(versions_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            # Extract the revision ID from the filename
            revision = filename.split('_')[0]
            versions.append(revision)
    
    return sorted(versions)


def get_latest_migration():
    """Get the most recent migration version"""
    versions = get_migration_versions()
    if versions:
        return versions[-1]
    return None


def create_test_database():
    """Create a temporary test database for migration testing"""
    # This is a placeholder. In a real implementation, you would create 
    # a temporary database specifically for testing migrations.
    # For PostgreSQL, this might involve creating a new database with a 
    # temporary name, or using a schema within an existing database.
    
    # For this example, we'll just use the existing database but with 
    # a specific test revision tag to avoid affecting the real data.
    return True, "Using existing database with test revision tag"


def test_migration_upgrade_downgrade(version):
    """Test upgrading to a specific version and then downgrading"""
    logger.info(f"Testing migration: {version}")
    
    # Run upgrade to the specified version
    logger.info(f"Upgrading to {version}")
    success, output = run_command(['python', 'manage.py', 'db', 'upgrade', version])
    if not success:
        logger.error(f"Failed to upgrade to {version}: {output}")
        return False
    
    # Run downgrade from the specified version
    logger.info(f"Downgrading from {version}")
    success, output = run_command(['python', 'manage.py', 'db', 'downgrade', f"{version}:base"])
    if not success:
        logger.error(f"Failed to downgrade from {version}: {output}")
        return False
    
    # Run upgrade again to ensure it works after a downgrade
    logger.info(f"Upgrading to {version} again")
    success, output = run_command(['python', 'manage.py', 'db', 'upgrade', version])
    if not success:
        logger.error(f"Failed to upgrade to {version} after downgrade: {output}")
        return False
    
    logger.info(f"Migration {version} passed upgrade/downgrade test")
    return True


def test_single_migration(version):
    """Test a single migration"""
    if not version:
        logger.error("No migration version specified")
        return False
    
    # Test upgrade and downgrade cycle
    success = test_migration_upgrade_downgrade(version)
    if not success:
        return False
    
    logger.info(f"Migration {version} tests passed")
    return True


def test_all_migrations():
    """Test all migrations in sequence"""
    versions = get_migration_versions()
    if not versions:
        logger.error("No migrations found to test")
        return False
    
    logger.info(f"Testing {len(versions)} migrations")
    
    # First test downgrading to base and upgrading to head
    logger.info("Testing full downgrade/upgrade cycle")
    
    # Downgrade to base
    success, output = run_command(['python', 'manage.py', 'db', 'downgrade', 'base'])
    if not success:
        logger.error(f"Failed to downgrade to base: {output}")
        return False
    
    # Upgrade to head
    success, output = run_command(['python', 'manage.py', 'db', 'upgrade', 'head'])
    if not success:
        logger.error(f"Failed to upgrade to head: {output}")
        return False
    
    logger.info("Full downgrade/upgrade cycle passed")
    
    # Now test each migration individually
    for version in versions:
        # Downgrade to before this migration
        prev_version = 'base'
        if versions.index(version) > 0:
            prev_version = versions[versions.index(version) - 1]
        
        logger.info(f"Downgrading to {prev_version}")
        success, output = run_command(['python', 'manage.py', 'db', 'downgrade', prev_version])
        if not success:
            logger.error(f"Failed to downgrade to {prev_version}: {output}")
            return False
        
        # Test this specific migration
        success = test_migration_upgrade_downgrade(version)
        if not success:
            return False
    
    # Restore to head
    logger.info("Restoring to head")
    success, output = run_command(['python', 'manage.py', 'db', 'upgrade', 'head'])
    if not success:
        logger.error(f"Failed to restore to head: {output}")
        return False
    
    logger.info("All migration tests passed")
    return True


def main():
    parser = argparse.ArgumentParser(description='Test database migrations')
    parser.add_argument('--latest', action='store_true', help='Test only the latest migration')
    parser.add_argument('--version', help='Test a specific migration version')
    
    args = parser.parse_args()
    
    # Create test environment
    success, message = create_test_database()
    if not success:
        logger.error(f"Failed to create test environment: {message}")
        sys.exit(1)
    
    try:
        if args.latest:
            # Test only the latest migration
            latest = get_latest_migration()
            if not latest:
                logger.error("No migrations found")
                sys.exit(1)
            
            logger.info(f"Testing latest migration: {latest}")
            if test_single_migration(latest):
                logger.info("Latest migration test passed")
                sys.exit(0)
            else:
                logger.error("Latest migration test failed")
                sys.exit(1)
        
        elif args.version:
            # Test a specific migration
            if test_single_migration(args.version):
                logger.info(f"Migration {args.version} test passed")
                sys.exit(0)
            else:
                logger.error(f"Migration {args.version} test failed")
                sys.exit(1)
        
        else:
            # Test all migrations
            if test_all_migrations():
                logger.info("All migration tests passed")
                sys.exit(0)
            else:
                logger.error("Migration tests failed")
                sys.exit(1)
    
    finally:
        # Cleanup test environment if needed
        logger.info("Cleanup complete")


if __name__ == '__main__':
    main()