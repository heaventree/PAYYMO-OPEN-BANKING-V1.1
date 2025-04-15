# Database Migration Guide

This document explains how to manage database migrations for the Payymo application.

## Overview

We use Alembic to manage database migrations, which is integrated with our Flask application. This ensures that all database schema changes are tracked, versioned, and can be applied or reverted in a controlled manner.

## Key Concepts

- **Migration**: A set of changes to be applied to the database schema
- **Revision**: A specific version of the database schema
- **Upgrade**: Apply migrations to advance the database schema
- **Downgrade**: Revert migrations to go back to a previous schema version

## Migration Files

Migration files are stored in the `migrations/versions` directory. Each file represents a set of changes and contains:

1. **Metadata**: Information about the migration, such as a unique identifier, dependencies, and description
2. **upgrade()**: Function containing operations to apply the changes
3. **downgrade()**: Function containing operations to revert the changes

## Command Line Tools

We provide several command-line tools to make working with migrations easier:

### 1. Basic Migration Commands (manage.py)

```bash
# Show current migration version
python manage.py db current

# Generate a new migration based on model changes
python manage.py db migrate -m "Add user preferences table"

# Apply all pending migrations
python manage.py db upgrade

# Revert the most recent migration
python manage.py db downgrade

# Show migration history
python manage.py db history

# Check if database is up to date with migrations
python manage.py db check
```

### 2. Safe Database Upgrade (db_upgrade.py)

This script provides additional safety checks when applying migrations.

```bash
# Apply migrations with confirmation prompt
python db_upgrade.py

# Just check if migrations are needed
python db_upgrade.py --check-only

# Create a backup before migrating
python db_upgrade.py --backup

# Skip confirmation prompt
python db_upgrade.py --force
```

### 3. Creating Migrations (create_migration.py)

This script simplifies the process of creating migrations with proper descriptions.

```bash
# Create a new migration with description
python create_migration.py "Add user preferences table"
```

## Best Practices

### When to Create Migrations

Create a new migration when:

1. Adding or removing a table
2. Adding, modifying, or removing columns
3. Adding or removing indexes or constraints
4. Any other change to the database schema

### Writing Good Migrations

1. **Descriptive messages**: Use clear, concise descriptions explaining the purpose of the migration
2. **Atomic changes**: Keep migrations focused on a single logical change
3. **Test both ways**: Make sure both upgrade and downgrade functions work correctly
4. **Data preservation**: When removing or changing columns, ensure that important data is preserved

### Running Migrations

1. **Development**: Use `python manage.py db upgrade` during development
2. **Staging/Testing**: Use `python db_upgrade.py --backup` to create a backup before applying
3. **Production**: Always use `python db_upgrade.py --backup` and review changes before confirming

## Troubleshooting

### Common Issues

1. **Migration conflicts**: If multiple developers create migrations simultaneously, conflicts may arise. Resolve by:
   - Creating a new migration that includes both sets of changes
   - Manually editing the conflicting migration files

2. **Failed migrations**: If a migration fails:
   - Check the error message for specific issues
   - Fix the issue in your models or migration script
   - For production: restore from backup if necessary

3. **Empty migrations**: If a migration has no changes:
   - Delete the migration file
   - Make sure your models have actually changed

### Getting Help

If you encounter issues with migrations:

1. Check the Alembic documentation: https://alembic.sqlalchemy.org/
2. Review the migration logs in the console output
3. Contact the database administrator or lead developer