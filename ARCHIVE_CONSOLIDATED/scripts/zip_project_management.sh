#!/bin/bash

# Create a timestamp for the zip file name
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="project_management_${TIMESTAMP}.zip"

# Create the zip file of just the project_management folder
echo "Creating zip file of project_management folder: $ZIP_NAME"
zip -r $ZIP_NAME project_management

echo "Zip file created: $ZIP_NAME"
echo "Size: $(du -h $ZIP_NAME | cut -f1)"