#!/usr/bin/env python3
"""
Database Migration Management Tool

This script provides a command-line interface for managing database migrations
using Alembic. It's integrated with the Flask application to ensure all models
are properly recognized and migrated.

Usage:
  python manage.py db init      # Initialize migrations (first time setup)
  python manage.py db migrate   # Generate a new migration based on model changes
  python manage.py db upgrade   # Apply migrations to the database
  python manage.py db downgrade # Revert to the previous migration
  python manage.py db current   # Show current migration version
  python manage.py db history   # Show migration history
"""

import os
import sys
import click
from alembic import command
from alembic.config import Config
from flask_backend.app import app, db


@click.group()
def cli():
    """Database migration management tool for Payymo"""
    pass


@cli.group()
def db():
    """Database migration commands"""
    pass


def get_alembic_config():
    """Get the Alembic configuration"""
    # Get the directory containing this script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Create the Alembic config
    config = Config(os.path.join(dir_path, 'alembic.ini'))
    config.set_main_option('script_location', os.path.join(dir_path, 'migrations'))
    
    # Override the sqlalchemy.url value from the Flask app config
    with app.app_context():
        config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
    
    return config


@db.command()
def init():
    """Initialize a new migration environment"""
    config = get_alembic_config()
    command.init(config, 'migrations')
    click.echo('Migration environment initialized.')


@db.command()
@click.option('-m', '--message', help='Migration message')
def migrate(message):
    """Generate a new migration based on model changes"""
    config = get_alembic_config()
    with app.app_context():
        command.revision(config, message=message, autogenerate=True)
    click.echo('Migration script generated.')


@db.command()
@click.option('--revision', default='head', help='Revision identifier')
def upgrade(revision):
    """Apply migrations to the database"""
    config = get_alembic_config()
    with app.app_context():
        command.upgrade(config, revision)
    click.echo(f'Database upgraded to {revision}.')


@db.command()
@click.option('--revision', default='-1', help='Revision identifier')
def downgrade(revision):
    """Revert to a previous migration"""
    config = get_alembic_config()
    with app.app_context():
        command.downgrade(config, revision)
    click.echo(f'Database downgraded to {revision}.')


@db.command()
def current():
    """Show current migration version"""
    config = get_alembic_config()
    with app.app_context():
        command.current(config)


@db.command()
def history():
    """Show migration history"""
    config = get_alembic_config()
    with app.app_context():
        command.history(config)


@db.command()
def check():
    """Check if there are any changes that need to be migrated"""
    config = get_alembic_config()
    from alembic.script import ScriptDirectory
    from alembic.migration import MigrationContext
    
    with app.app_context():
        script = ScriptDirectory.from_config(config)
        
        # Get connection from Flask-SQLAlchemy
        connection = db.engine.connect()
        
        try:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            # Get the latest revision in the migration scripts
            head_rev = script.get_current_head()
            
            if head_rev != current_rev:
                click.echo(f"Database is at revision {current_rev or 'None'}")
                click.echo(f"Migration scripts head is at {head_rev or 'None'}")
                click.echo("Database is not up to date. Run 'manage.py db upgrade' to apply migrations.")
                return False
            else:
                click.echo("Database is up to date.")
                return True
        finally:
            connection.close()


if __name__ == '__main__':
    cli()