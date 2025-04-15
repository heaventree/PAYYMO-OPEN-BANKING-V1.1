"""
Migration Utility Functions

This module provides utility functions for working with database migrations
from within the application code. It allows checking migration status,
applying migrations, and other operations.
"""

import os
import sys
import subprocess
import logging
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)


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


def check_migrations_status():
    """
    Check if the database is up to date with migrations
    
    Returns:
        tuple: (is_up_to_date, status_message)
    """
    success, output = run_command(['python', 'manage.py', 'db', 'check'])
    
    if not success:
        logger.error(f"Failed to check migration status: {output}")
        return False, f"Error checking migrations: {output}"
    
    if "Database is up to date" in output:
        return True, "Database schema is up to date"
    else:
        return False, "Database schema requires migration"


def get_migration_history():
    """
    Get the migration history
    
    Returns:
        tuple: (success, history_text)
    """
    success, output = run_command(['python', 'manage.py', 'db', 'history'])
    
    if not success:
        logger.error(f"Failed to get migration history: {output}")
        return False, f"Error getting migration history: {output}"
    
    return True, output


def get_current_revision():
    """
    Get the current migration revision
    
    Returns:
        tuple: (success, current_revision)
    """
    success, output = run_command(['python', 'manage.py', 'db', 'current'])
    
    if not success:
        logger.error(f"Failed to get current revision: {output}")
        return False, None
    
    # Parse the output to extract the revision
    for line in output.splitlines():
        if "current" in line.lower() and ":" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                revision = parts[1].strip()
                return True, revision
    
    return True, None  # No revision found (database might be empty)


def check_database_schema_validation():
    """
    Validate all models against the current database schema to detect discrepancies
    
    Returns:
        tuple: (is_valid, validation_message)
    """
    # This function would contain custom logic to validate the database schema
    # against the models. This is project-specific and would depend on
    # the ORM and models being used.
    
    # For now, we'll just use Alembic's check command as a proxy
    success, output = run_command(['python', 'manage.py', 'db', 'check'])
    
    if not success:
        logger.error(f"Failed to validate database schema: {output}")
        return False, f"Error validating database schema: {output}"
    
    if "Database is up to date" in output:
        return True, "Database schema matches models"
    else:
        return False, "Database schema doesn't match models"


def auto_migrate(confirm=True):
    """
    Automatically apply any pending migrations
    
    Args:
        confirm (bool): Whether to require confirmation before applying
        
    Returns:
        tuple: (success, message)
    """
    # First check if migrations are needed
    is_up_to_date, _ = check_migrations_status()
    
    if is_up_to_date:
        return True, "No migrations needed, database is up to date"
    
    # Use the db_upgrade.py script for safer migration with additional checks
    cmd = ['python', 'db_upgrade.py']
    
    if not confirm:
        cmd.append('--force')
    
    success, output = run_command(cmd)
    
    if success:
        return True, "Migrations applied successfully"
    else:
        logger.error(f"Failed to apply migrations: {output}")
        return False, f"Error applying migrations: {output}"


def register_migration_commands(app):
    """
    Register migration-related CLI commands with the Flask application
    
    Args:
        app: Flask application instance
    """
    import click
    
    @app.cli.group()
    def migrations():
        """Database migration commands."""
        pass
    
    @migrations.command()
    def status():
        """Show migration status."""
        is_up_to_date, message = check_migrations_status()
        click.echo(message)
    
    @migrations.command()
    def history():
        """Show migration history."""
        _, history = get_migration_history()
        click.echo(history)
    
    @migrations.command()
    def current():
        """Show current migration revision."""
        _, revision = get_current_revision()
        click.echo(f"Current revision: {revision or 'None'}")
    
    @migrations.command()
    @click.option('--force', is_flag=True, help='Skip confirmation prompt')
    def upgrade(force):
        """Apply pending migrations."""
        success, message = auto_migrate(confirm=not force)
        click.echo(message)