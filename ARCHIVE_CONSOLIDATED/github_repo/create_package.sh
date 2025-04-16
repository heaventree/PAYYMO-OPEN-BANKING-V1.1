#!/bin/bash

# Payymo Packaging Script
# This script creates a ready-to-install package for the Payymo integration.

echo "Creating Payymo installation package..."

# Create temporary directory
TEMP_DIR="payymo_package"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Create directory structure
mkdir -p $TEMP_DIR/whmcs_module
mkdir -p $TEMP_DIR/flask_backend
mkdir -p $TEMP_DIR/docs

# Copy WHMCS module files
echo "Copying WHMCS module files..."
cp -r package_for_installation/modules $TEMP_DIR/whmcs_module/

# Copy Flask backend files
echo "Copying Flask backend files..."
cp -r flask_backend $TEMP_DIR/
cp main.py $TEMP_DIR/
cp payymo_requirements.txt $TEMP_DIR/
cp install_backend.sh $TEMP_DIR/

# Copy documentation
echo "Copying documentation..."
cp INSTALL.md $TEMP_DIR/
cp README.md $TEMP_DIR/
cp CHANGELOG.md $TEMP_DIR/
cp -r docs $TEMP_DIR/

# Create the zip file
echo "Creating zip archive..."
ZIP_FILE="payymo_$(date +%Y%m%d).zip"
zip -r $ZIP_FILE $TEMP_DIR

# Clean up
rm -rf $TEMP_DIR

echo "Package created: $ZIP_FILE"
echo "You can now download this file and install according to INSTALL.md"