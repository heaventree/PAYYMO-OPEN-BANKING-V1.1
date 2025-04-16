#!/usr/bin/env python3
"""
Create Database Migration Script

This script simplifies the process of creating a new database migration.
It ensures proper descriptions and handles common edge cases.

Usage:
  python create_migration.py "Add user preferences table"

The script will:
1. Generate a well-formatted migration with the provided description
2. Run validation checks on the migration
3. Display a summary of the changes that will be made
"""

import os
import sys
import subprocess
import datetime
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('create_migration')


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


def create_migration(description):
    """Create a new migration with the given description"""
    if not description:
        logger.error("Migration description is required")
        return False, None
    
    # Sanitize description for command line
    safe_description = description.replace('"', '\\"')
    
    # Create migration
    logger.info(f"Creating migration: {description}")
    success, output = run_command(['python', 'manage.py', 'db', 'migrate', '-m', safe_description])
    
    if not success:
        logger.error(f"Failed to create migration: {output}")
        return False, None
    
    # Parse the output to find the migration filename
    migration_file = None
    for line in output.splitlines():
        if '/versions/' in line and '.py' in line:
            parts = line.split('/')
            for part in parts:
                if part.endswith('.py'):
                    migration_file = part
                    break
    
    if not migration_file:
        logger.warning("Created migration but couldn't identify the migration file")
    else:
        logger.info(f"Created migration file: {migration_file}")
    
    return True, migration_file


def verify_migration(migration_file):
    """Verify that the migration is valid"""
    if not migration_file:
        return False
    
    migration_path = os.path.join('migrations', 'versions', migration_file)
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file does not exist: {migration_path}")
        return False
    
    # Check if file is properly formatted
    with open(migration_path, 'r') as f:
        content = f.read()
        
        # Check for basic structure
        if 'def upgrade()' not in content or 'def downgrade()' not in content:
            logger.error("Migration file is missing upgrade or downgrade function")
            return False
        
        # Check for empty upgrade/downgrade (possible indication of no changes)
        if 'def upgrade():\n    pass' in content and 'def downgrade():\n    pass' in content:
            logger.warning("Migration appears to be empty (no changes detected)")
            return False
    
    logger.info("Migration verification passed")
    return True


def summarize_migration(migration_file):
    """Generate a summary of the changes in the migration"""
    if not migration_file:
        return
    
    migration_path = os.path.join('migrations', 'versions', migration_file)
    
    # Extract revision ID and description
    revision_id = migration_file.split('_')[0]
    
    # Read migration file to extract summary
    with open(migration_path, 'r') as f:
        content = f.readlines()
    
    # Find the migration description
    description = "Unknown"
    for line in content:
        if line.startswith('"""') and len(content) > content.index(line) + 1:
            description = content[content.index(line) + 1].strip()
            break
    
    # Extract operations from upgrade function
    operations = []
    in_upgrade = False
    for line in content:
        if 'def upgrade()' in line:
            in_upgrade = True
            continue
        if 'def downgrade()' in line:
            in_upgrade = False
            continue
        if in_upgrade and line.strip() and not line.strip().startswith('#'):
            operations.append(line.strip())
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Migration Summary for: {revision_id}")
    print(f"Description: {description}")
    print("-" * 60)
    print("Operations to be performed:")
    for i, op in enumerate(operations, 1):
        if 'op.create_table' in op:
            print(f"  {i}. Create new table")
        elif 'op.drop_table' in op:
            print(f"  {i}. Drop table")
        elif 'op.add_column' in op:
            print(f"  {i}. Add column")
        elif 'op.drop_column' in op:
            print(f"  {i}. Drop column")
        elif 'op.create_index' in op:
            print(f"  {i}. Create index")
        elif 'op.drop_index' in op:
            print(f"  {i}. Drop index")
        elif 'op.create_foreign_key' in op:
            print(f"  {i}. Create foreign key")
        elif 'op.drop_constraint' in op:
            print(f"  {i}. Drop constraint")
        elif 'op.alter_column' in op:
            print(f"  {i}. Alter column")
        else:
            print(f"  {i}. {op[:60]}..." if len(op) > 60 else f"  {i}. {op}")
    
    print("=" * 60)
    print("To apply this migration, run:")
    print("  python manage.py db upgrade\n")


def main():
    parser = argparse.ArgumentParser(description='Create a new database migration')
    parser.add_argument('description', nargs='?', help='Description of the migration')
    parser.add_argument('--message', '-m', help='Alternative way to provide migration description')
    
    args = parser.parse_args()
    
    # Get description from arguments
    description = args.description or args.message
    
    if not description:
        parser.print_help()
        sys.exit(1)
    
    # Create migration
    success, migration_file = create_migration(description)
    if not success:
        sys.exit(1)
    
    # Verify migration
    if not verify_migration(migration_file):
        logger.error("Migration verification failed")
        sys.exit(1)
    
    # Generate summary
    summarize_migration(migration_file)
    
    logger.info("Migration creation completed successfully")


if __name__ == '__main__':
    main()