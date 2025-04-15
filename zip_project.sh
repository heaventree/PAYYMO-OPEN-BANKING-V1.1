#!/bin/bash

# Create a timestamp for the zip file name
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="payymo_${TIMESTAMP}.zip"

# Directories to exclude from the zip
EXCLUDE_DIRS=(
  "backups/*"
  "ARCHIVE/*"
  "__pycache__/*"
  "*/__pycache__/*"
  "*.pyc"
)

# Build the exclude arguments
EXCLUDE_ARGS=""
for dir in "${EXCLUDE_DIRS[@]}"; do
  EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$dir"
done

# Create the zip file
echo "Creating zip file: $ZIP_NAME"
zip -r $ZIP_NAME . $EXCLUDE_ARGS

echo "Zip file created: $ZIP_NAME"
echo "Size: $(du -h $ZIP_NAME | cut -f1)"