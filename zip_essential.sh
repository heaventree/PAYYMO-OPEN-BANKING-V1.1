#!/bin/bash

# Create a timestamp for the zip file name
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="payymo_essential_${TIMESTAMP}.zip"

# Directories to include in the zip
INCLUDE_DIRS=(
  "flask_backend"
  "project_management"
  "whmcs_module"
  "certs"
  "tests"
  "main.py"
  "requirements.txt"
  "payymo_requirements.txt"
  "README.md"
)

# Create the zip file
echo "Creating essential zip file: $ZIP_NAME"
zip -r $ZIP_NAME "${INCLUDE_DIRS[@]}"

echo "Zip file created: $ZIP_NAME"
echo "Size: $(du -h $ZIP_NAME | cut -f1)"