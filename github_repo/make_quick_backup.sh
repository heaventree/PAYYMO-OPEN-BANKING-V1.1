#!/bin/bash
# Quick Backup Script
# Run this before making any potentially disruptive changes

# Create timestamp for backup folder
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Ask for a description of the changes
echo "Enter a brief description of the changes you're about to make:"
read CHANGE_DESCRIPTION

# Create README with change description
echo "Backup created before: $CHANGE_DESCRIPTION" > "$BACKUP_DIR/README.md"
echo "Timestamp: $(date)" >> "$BACKUP_DIR/README.md"
echo "Files included: templates, static, routes.py" >> "$BACKUP_DIR/README.md"

# Copy important directories
echo "Creating backup in $BACKUP_DIR..."
cp -r ./flask_backend/templates "$BACKUP_DIR/"
cp -r ./flask_backend/static "$BACKUP_DIR/"
cp ./flask_backend/routes.py "$BACKUP_DIR/"
cp ./flask_backend/routes_test_data.py "$BACKUP_DIR/" 2>/dev/null
cp ./flask_backend/routes_testing.py "$BACKUP_DIR/" 2>/dev/null
cp ./main.py "$BACKUP_DIR/"

# List all files that were backed up
echo "Backup complete. The following files were backed up:"
find "$BACKUP_DIR" -type f | grep -v "README.md" | sort

echo "Backup created successfully in $BACKUP_DIR"
echo "Remember to test your changes after implementation!"