# Database Migration System

## Overview
The database migration system provides a robust mechanism for safely applying database schema changes across environments. It includes utilities for creating, verifying, and applying migrations with safety checks and rollback capabilities.

## Key Components

### 1. Migration Utilities (`flask_backend/utils/migrations.py`)
- Database connection and verification functions
- Table and column existence checking
- Data backup functionality
- Migration script application
- Database integrity verification

### 2. Migration Creation Script (`create_migration.py`)
- Simplified process for creating new migrations
- Automatic safety checks and enhancements
- Migration verification and validation
- Summary of changes to be applied

### 3. Database Upgrade Script (`db_upgrade.py`)
- Safe application of pending migrations
- Database backup functionality
- Pre and post-migration verification
- Command-line interface with safety confirmations

### 4. Flask CLI Commands
- Registered through `register_migration_commands()`
- Available through `flask db_operations` command group
- Commands for init, migrate, upgrade, downgrade, etc.
- Additional verification and backup commands

## Using Migrations

### Creating a New Migration

To create a new migration:

```bash
python create_migration.py "Description of the migration"
```

This will:
1. Generate a well-formatted migration with the appropriate filename
2. Add safety checks for table and column existence
3. Create proper upgrade and downgrade functions
4. Display a summary of the changes to be made

### Applying Migrations

To apply pending migrations:

```bash
python db_upgrade.py
```

Or using Flask CLI:

```bash
flask db_operations upgrade
```

This will:
1. Check database connectivity
2. Verify database state before migration
3. Apply pending migrations
4. Verify database integrity after migration

### Verifying Database Status

To check if the database is up to date:

```bash
flask db_operations check
```

To verify database integrity:

```bash
flask db_operations verify
```

### Creating Database Backups

To create backups of all tables:

```bash
flask db_operations backup --prefix custom_name
```

## Safety Features

### Table Existence Checks
Migrations automatically check if tables exist before attempting to create them:

```python
def upgrade():
    if not has_table(op.get_bind(), 'users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True),
            # ...
        )
```

### Column Existence Checks
Migrations verify column existence before adding or modifying columns:

```python
def upgrade():
    if has_table(op.get_bind(), 'users') and not column_exists(op.get_bind(), 'users', 'email'):
        op.add_column('users', sa.Column('email', sa.String(255)))
```

### Database Backups
Before applying potentially destructive changes, the system can create backups:

```python
def upgrade():
    # Backup table before making changes
    create_table_backup('users', 'before_email_addition')
    
    # Add new column
    op.add_column('users', sa.Column('email', sa.String(255)))
```

## Best Practices

1. **Always Use Migrations**: Avoid using `db.create_all()` in production code.
2. **Test Migrations**: Run migrations in a test environment before production.
3. **Include Downgrade Functions**: Always provide a way to reverse migrations.
4. **Use Safety Checks**: Include table and column existence checks in all migrations.
5. **Backup Before Changes**: Create backups before potentially destructive operations.
6. **Keep Migrations Focused**: Each migration should address a specific change.
7. **Review Migration Summaries**: Check the summary output before applying migrations.

## Troubleshooting

### Common Issues

1. **Table Already Exists**
   - Use table existence checks to prevent errors
   - Example: `if not has_table(op.get_bind(), 'table_name')`

2. **Column Already Exists**
   - Use column existence checks
   - Example: `if not column_exists(op.get_bind(), 'table_name', 'column_name')`

3. **Foreign Key Constraints**
   - Create tables in the correct order
   - Drop constraints before dropping tables

4. **Data Loss Warnings**
   - Review migrations carefully when data loss warnings appear
   - Create data backups before applying such migrations

## Migration Structure

A typical migration file contains:

```python
"""Migration description

Revision ID: abc123
Revises: previous_revision
Create Date: 2025-04-15 10:30:00

"""

# Import required libraries
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# Helper functions
def has_table(conn, table_name):
    """Check if a table exists in the database"""
    return inspect(conn).has_table(table_name)

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    columns = [col['name'] for col in inspect(conn).get_columns(table_name)]
    return column_name in columns

# Revision identifiers
revision = 'abc123'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    """Apply the migration"""
    # Example: Create a new table with safety check
    if not has_table(op.get_bind(), 'new_table'):
        op.create_table(
            'new_table',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('created_at', sa.DateTime(), default=sa.func.now())
        )
    
    # Example: Add a column with safety check
    if has_table(op.get_bind(), 'existing_table') and not column_exists(op.get_bind(), 'existing_table', 'new_column'):
        op.add_column('existing_table', sa.Column('new_column', sa.String(255)))

def downgrade():
    """Revert the migration"""
    # Example: Drop column
    if has_table(op.get_bind(), 'existing_table') and column_exists(op.get_bind(), 'existing_table', 'new_column'):
        op.drop_column('existing_table', 'new_column')
    
    # Example: Drop table
    if has_table(op.get_bind(), 'new_table'):
        op.drop_table('new_table')
```

## Conclusion

The enhanced migration system provides robust tools for managing database schema changes safely and consistently across environments. By following the outlined best practices and leveraging the built-in safety features, you can ensure reliable database evolution throughout the application lifecycle.