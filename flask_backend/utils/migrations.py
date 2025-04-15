"""
Migration Utilities

This module provides helper functions for working with database migrations.
It includes functions for safely applying migrations, verifying schema integrity,
and handling common migration operations.
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Union

from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session

import logging

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name, level=logging.INFO):
    """Get a logger with standard configuration"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)
    return logger

logger = get_logger('flask_backend.utils.migrations')

def get_database_url() -> str:
    """Get the database URL from environment, with fallback to development DB"""
    return os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/payymo')

def get_database_engine(database_url: Optional[str] = None):
    """Create a database engine with proper connection settings"""
    if database_url is None:
        database_url = get_database_url()
    
    return create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections after 5 minutes
        pool_size=5,         # Maximum number of connections in pool
        max_overflow=10      # Maximum number of connections that can be created beyond pool_size
    )

def check_database_connection() -> bool:
    """Check if the database is accessible"""
    try:
        engine = get_database_engine()
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def list_tables() -> List[str]:
    """List all tables in the database"""
    try:
        engine = get_database_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables
    except SQLAlchemyError as e:
        logger.error(f"Failed to list tables: {str(e)}")
        return []

def get_table_columns(table_name: str) -> List[Dict[str, Any]]:
    """Get column information for a specific table"""
    try:
        engine = get_database_engine()
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return columns
    except SQLAlchemyError as e:
        logger.error(f"Failed to get columns for table {table_name}: {str(e)}")
        return []

def get_table_indexes(table_name: str) -> List[Dict[str, Any]]:
    """Get index information for a specific table"""
    try:
        engine = get_database_engine()
        inspector = inspect(engine)
        indexes = inspector.get_indexes(table_name)
        return indexes
    except SQLAlchemyError as e:
        logger.error(f"Failed to get indexes for table {table_name}: {str(e)}")
        return []

def get_table_constraints(table_name: str) -> List[Dict[str, Any]]:
    """Get constraint information for a specific table"""
    try:
        engine = get_database_engine()
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        unique_constraints = inspector.get_unique_constraints(table_name)
        
        constraints = []
        if primary_keys:
            constraints.append({
                'type': 'primary',
                'name': primary_keys.get('name'),
                'columns': primary_keys.get('constrained_columns', [])
            })
        
        for fk in foreign_keys:
            constraints.append({
                'type': 'foreign',
                'name': fk.get('name'),
                'columns': fk.get('constrained_columns', []),
                'referred_table': fk.get('referred_table'),
                'referred_columns': fk.get('referred_columns', [])
            })
        
        for uc in unique_constraints:
            constraints.append({
                'type': 'unique',
                'name': uc.get('name'),
                'columns': uc.get('column_names', [])
            })
        
        return constraints
    except SQLAlchemyError as e:
        logger.error(f"Failed to get constraints for table {table_name}: {str(e)}")
        return []

def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    try:
        engine = get_database_engine()
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except SQLAlchemyError as e:
        logger.error(f"Failed to check if table {table_name} exists: {str(e)}")
        return False

def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        if not table_exists(table_name):
            return False
            
        engine = get_database_engine()
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except SQLAlchemyError as e:
        logger.error(f"Failed to check if column {column_name} exists in table {table_name}: {str(e)}")
        return False

def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table"""
    try:
        if not table_exists(table_name):
            return False
            
        engine = get_database_engine()
        inspector = inspect(engine)
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except SQLAlchemyError as e:
        logger.error(f"Failed to check if index {index_name} exists on table {table_name}: {str(e)}")
        return False

def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Check if a constraint exists on a table"""
    try:
        if not table_exists(table_name):
            return False
            
        engine = get_database_engine()
        inspector = inspect(engine)
        
        # Check foreign key constraints
        fks = inspector.get_foreign_keys(table_name)
        if any(fk.get('name') == constraint_name for fk in fks):
            return True
        
        # Check primary key constraint
        pk = inspector.get_pk_constraint(table_name)
        if pk.get('name') == constraint_name:
            return True
        
        # Check unique constraints
        ucs = inspector.get_unique_constraints(table_name)
        if any(uc.get('name') == constraint_name for uc in ucs):
            return True
        
        return False
    except SQLAlchemyError as e:
        logger.error(f"Failed to check if constraint {constraint_name} exists on table {table_name}: {str(e)}")
        return False

def copy_table_data(source_table: str, target_table: str, engine=None) -> bool:
    """Copy data from one table to another with the same structure"""
    if engine is None:
        engine = get_database_engine()
    
    try:
        with Session(engine) as session:
            # Check that both tables exist
            if not table_exists(source_table) or not table_exists(target_table):
                logger.error(f"Source or target table does not exist")
                return False
                
            # Get columns that exist in both tables for safe copying
            source_cols = {col['name'] for col in get_table_columns(source_table)}
            target_cols = {col['name'] for col in get_table_columns(target_table)}
            common_cols = list(source_cols.intersection(target_cols))
            
            if not common_cols:
                logger.error(f"No common columns between {source_table} and {target_table}")
                return False
            
            # Build column list for the copy operation
            col_list = ", ".join(common_cols)
            
            # Copy data
            query = f"INSERT INTO {target_table} ({col_list}) SELECT {col_list} FROM {source_table}"
            session.execute(query)
            session.commit()
            logger.info(f"Successfully copied data from {source_table} to {target_table}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to copy data from {source_table} to {target_table}: {str(e)}")
        return False

def create_table_backup(table_name: str, suffix: Optional[str] = None) -> Optional[str]:
    """Create a backup of a table by copying its structure and data"""
    try:
        if not table_exists(table_name):
            logger.error(f"Table {table_name} does not exist, cannot create backup")
            return None
        
        # Generate backup table name
        timestamp = int(time.time())
        if suffix:
            backup_table = f"{table_name}_bak_{suffix}_{timestamp}"
        else:
            backup_table = f"{table_name}_bak_{timestamp}"
        
        engine = get_database_engine()
        with Session(engine) as session:
            # Create new table with same structure
            session.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table_name}")
            session.commit()
            
            logger.info(f"Created backup table {backup_table}")
            return backup_table
    except SQLAlchemyError as e:
        logger.error(f"Failed to create backup of table {table_name}: {str(e)}")
        return None

def apply_migration_script(script_path: str) -> bool:
    """Apply a migration script to the database"""
    try:
        with open(script_path, 'r') as f:
            sql = f.read()
        
        engine = get_database_engine()
        with Session(engine) as session:
            session.execute(sql)
            session.commit()
            logger.info(f"Successfully applied migration script: {script_path}")
            return True
    except (IOError, SQLAlchemyError) as e:
        logger.error(f"Failed to apply migration script {script_path}: {str(e)}")
        return False

def get_table_row_count(table_name: str) -> int:
    """Get the number of rows in a table"""
    try:
        engine = get_database_engine()
        with Session(engine) as session:
            result = session.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = result.scalar()
            return count
    except SQLAlchemyError as e:
        logger.error(f"Failed to get row count for table {table_name}: {str(e)}")
        return -1

def verify_database_integrity() -> Dict[str, Any]:
    """
    Perform basic checks to verify database integrity
    
    Returns a dictionary with verification results
    """
    results = {
        'success': True,
        'connection': False,
        'tables': [],
        'issues': []
    }
    
    # Check connection
    if not check_database_connection():
        results['success'] = False
        results['issues'].append("Database connection failed")
        return results
    
    results['connection'] = True
    
    # Check tables
    tables = list_tables()
    results['tables'] = tables
    
    if not tables:
        results['success'] = False
        results['issues'].append("No tables found in database")
    
    # Check for specific required tables
    required_tables = [
        'license_keys', 'whmcs_instances', 'bank_connections', 
        'stripe_connections', 'transactions', 'stripe_payments'
    ]
    
    missing_tables = [table for table in required_tables if table not in tables]
    if missing_tables:
        results['success'] = False
        results['issues'].append(f"Missing required tables: {', '.join(missing_tables)}")
    
    # Check alembic version table
    if 'alembic_version' not in tables:
        results['success'] = False
        results['issues'].append("Alembic version table not found")
    
    return results

def check_migrations_status():
    """
    Check if the database is up to date with migrations
    
    Returns:
        Tuple[bool, str]: (is_up_to_date, message)
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.environment import EnvironmentContext
        from alembic import command
        
        config = Config('alembic.ini')
        script = ScriptDirectory.from_config(config)
        
        # Get current head revision
        heads = script.get_revisions('head')
        head_revs = [r.revision for r in heads]
        
        # Get current database revision
        def get_current_rev(rev, context):
            return rev
            
        with EnvironmentContext(config, script, fn=get_current_rev) as env:
            conn = env.get_connection()
            current_rev = env.get_current_revision()
        
        if current_rev in head_revs:
            return True, "Database is up to date"
        else:
            return False, f"Database is at revision {current_rev}, but latest is {head_revs[0]}"
    
    except Exception as e:
        logger.error(f"Error checking migration status: {str(e)}")
        return False, f"Error checking migrations: {str(e)}"

def register_migration_commands(app, db):
    """
    Register migration commands with the Flask CLI
    
    This function adds migration-related commands to the Flask CLI.
    It should be called from the main app.py file.
    
    Args:
        app: The Flask application instance
        db: The SQLAlchemy database instance
    """
    import click
    from alembic import command
    from alembic.config import Config
    from flask.cli import with_appcontext
    
    @app.cli.group()
    def db_operations():
        """Database migration operations."""
        pass
    
    @db_operations.command('init')
    @with_appcontext
    def init():
        """Initialize the migration repository."""
        config = Config('alembic.ini')
        command.init(config, 'migrations', template='flask')
        click.echo('Initialized the migration repository.')
    
    @db_operations.command('migrate')
    @click.option('--message', '-m', default=None, help='Migration message')
    @click.option('--autogenerate', '-a', is_flag=True, default=True, help='Autogenerate migration')
    @with_appcontext
    def migrate(message, autogenerate):
        """Generate a new migration."""
        config = Config('alembic.ini')
        if autogenerate:
            command.revision(config, message, autogenerate=True)
        else:
            command.revision(config, message, autogenerate=False)
        click.echo('Generated new migration.')
    
    @db_operations.command('upgrade')
    @click.option('--revision', default='head', help='Revision to upgrade to')
    @with_appcontext
    def upgrade(revision):
        """Upgrade to a later revision."""
        # Check database connection first
        if not check_database_connection():
            click.echo('Error: Database connection failed')
            return
            
        # Verify tables before upgrade
        tables_before = list_tables()
        
        # Perform the upgrade
        config = Config('alembic.ini')
        command.upgrade(config, revision)
        click.echo(f'Upgraded to revision {revision}.')
        
        # Verify tables after upgrade
        tables_after = list_tables()
        new_tables = [t for t in tables_after if t not in tables_before]
        if new_tables:
            click.echo(f'Created new tables: {", ".join(new_tables)}')
    
    @db_operations.command('downgrade')
    @click.option('--revision', required=True, help='Revision to downgrade to')
    @with_appcontext
    def downgrade(revision):
        """Revert to a previous revision."""
        # Safety warning for production
        if os.environ.get('FLASK_ENV') == 'production':
            if not click.confirm('WARNING: You are about to downgrade the database in PRODUCTION. Continue?'):
                click.echo('Downgrade cancelled.')
                return
                
        # Perform the downgrade
        config = Config('alembic.ini')
        command.downgrade(config, revision)
        click.echo(f'Downgraded to revision {revision}.')
    
    @db_operations.command('current')
    @with_appcontext
    def current():
        """Show current revision."""
        config = Config('alembic.ini')
        command.current(config)
    
    @db_operations.command('history')
    @click.option('--verbose', '-v', is_flag=True, default=False, help='Show verbose output')
    @with_appcontext
    def history(verbose):
        """Show revision history."""
        config = Config('alembic.ini')
        command.history(config, verbose=verbose)
    
    @db_operations.command('check')
    @with_appcontext
    def check():
        """Check if database is up to date."""
        config = Config('alembic.ini')
        script = command._script_from_config(config)
        heads = script.get_revisions('head')
        head_revs = set(heads)
        
        try:
            context = command._get_config_context(config)
            current_rev = context.get_current_revision()
            
            if current_rev in head_revs:
                click.echo('Database is up to date.')
            else:
                click.echo('Database is not up to date. Run upgrade to apply migrations.')
        except Exception as e:
            click.echo(f'Error checking migration status: {e}')
    
    @db_operations.command('verify')
    @with_appcontext
    def verify():
        """Verify database integrity."""
        results = verify_database_integrity()
        
        if results['success']:
            click.echo('Database integrity check passed.')
            click.echo(f"Found {len(results['tables'])} tables.")
        else:
            click.echo('Database integrity check failed:')
            for issue in results['issues']:
                click.echo(f" - {issue}")
    
    @db_operations.command('backup')
    @click.option('--prefix', default=None, help='Backup name prefix')
    @with_appcontext
    def backup(prefix):
        """Create a backup of all tables."""
        timestamp = int(time.time())
        suffix = prefix or f"backup_{timestamp}"
        
        tables = list_tables()
        successful = 0
        
        for table in tables:
            if create_table_backup(table, suffix):
                successful += 1
                
        if successful == len(tables):
            click.echo(f'Successfully backed up {successful} tables with suffix "{suffix}".')
        else:
            click.echo(f'Backed up {successful} out of {len(tables)} tables with suffix "{suffix}".')
            
    return db_operations