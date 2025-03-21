#!/usr/bin/env python3
"""
Backup chat script that saves conversation to JSON files every 15 minutes.
Run in the background with: nohup python3 backup_chat.py &
"""

import json
import os
import re
import time
import datetime
import shutil
from pathlib import Path

# Configuration
BACKUP_DIR = "backups"  # Internal backups
GITHUB_BACKUP_DIR = "github_ready_backups"  # GitHub-ready backups
CODE_SNIPPETS_FILE = os.path.join(GITHUB_BACKUP_DIR, "code_snippets.json")
INTERVAL_SECONDS = 15 * 60  # 15 minutes
MAX_BACKUPS = 10  # Keep last 10 backups

# Important files to always include in backups
KEY_FILES = [
    "main.py",
    "flask_backend/app.py",
    "flask_backend/routes.py",
    "flask_backend/models.py",
    "flask_backend/services/gocardless_service.py",
    "flask_backend/services/invoice_matching_service.py",
    "flask_backend/static/js/main.js",
    "flask_backend/static/js/bank_wizard.js",
    "flask_backend/static/css/style.css",
    "flask_backend/templates/dashboard.html",
    "flask_backend/templates/components/bank_connection_wizard.html",
    "flask_backend/templates/components/financial_goals.html",
    "flask_backend/templates/components/feature_card_template.html",
    "flask_backend/ui_standards.md",
    "flask_backend/UI_DEVELOPER_README.md",
]

# Ensure backup directories exist
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(GITHUB_BACKUP_DIR, exist_ok=True)

def create_github_backup():
    """Create a GitHub-ready backup of important files"""
    # Current date for versioning
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Create version directories
    version_dir = os.path.join(GITHUB_BACKUP_DIR, f"version_{date_str}")
    os.makedirs(version_dir, exist_ok=True)
    
    # Back up key files for GitHub
    for file_path in KEY_FILES:
        if os.path.exists(file_path):
            # Create the directory structure
            target_path = os.path.join(version_dir, os.path.dirname(file_path))
            os.makedirs(target_path, exist_ok=True)
            
            # Copy the file
            try:
                shutil.copy2(file_path, os.path.join(version_dir, file_path))
            except Exception as e:
                print(f"Error backing up to GitHub dir {file_path}: {e}")
    
    # Create a version file
    version_info = os.path.join(version_dir, "version_info.md")
    with open(version_info, 'w') as f:
        f.write(f"# Payymo Open Banking Integration - Version {date_str}\n\n")
        f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")
        f.write("## Files Included\n\n")
        for file_path in KEY_FILES:
            if os.path.exists(os.path.join(version_dir, file_path)):
                f.write(f"- `{file_path}`\n")
    
    # Create a README in the main directory if it doesn't exist
    readme_path = os.path.join(GITHUB_BACKUP_DIR, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write("# Payymo Open Banking Integration Backups\n\n")
            f.write("This directory contains versioned backups of the codebase.\n\n")
            f.write("## Latest Version\n\n")
            f.write(f"- [Version {date_str}](version_{date_str}/version_info.md)\n")
    else:
        # Update the README with the latest version
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Update the latest version section
        latest_version_line = f"- [Version {date_str}](version_{date_str}/version_info.md)"
        if "## Latest Version" in content:
            new_content = re.sub(r"## Latest Version\s+\n.*", f"## Latest Version\n\n{latest_version_line}", content, flags=re.DOTALL)
            with open(readme_path, 'w') as f:
                f.write(new_content)
    
    print(f"GitHub-ready backup created at: {version_dir}")
    return version_dir

def create_backup():
    """Create a backup of the current chat state"""
    # Create date-specific directory
    date_dir = os.path.join(BACKUP_DIR, datetime.datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%H-%M-%S")
    backup_dir = os.path.join(date_dir, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create the code snippets file if it doesn't exist
    if not os.path.exists(CODE_SNIPPETS_FILE):
        with open(CODE_SNIPPETS_FILE, 'w') as f:
            json.dump({
                "project": "Payymo Open Banking Integration",
                "snippets": {}
            }, f, indent=2)
    
    # Backup important files
    backup_files(backup_dir)
    
    # Also create a GitHub-ready backup
    github_backup_dir = create_github_backup()
    
    # Create a summary file
    summary_file = os.path.join(backup_dir, "backup_info.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Backup created at {datetime.datetime.now().isoformat()}\n")
        f.write(f"Project: Payymo Open Banking Integration\n\n")
        f.write("Files included:\n")
        for root, _, files in os.walk(backup_dir):
            for file in files:
                if file != "backup_info.txt":
                    f.write(f"- {os.path.join(root, file)[len(backup_dir)+1:]}\n")
    
    print(f"Backup created: {backup_dir}")
    return backup_dir

def backup_files(backup_dir):
    """Back up key files to the specified backup directory"""
    # Create necessary subdirectories
    for file_path in KEY_FILES:
        if os.path.exists(file_path):
            # Create the directory structure
            target_path = os.path.join(backup_dir, os.path.dirname(file_path))
            os.makedirs(target_path, exist_ok=True)
            
            # Copy the file
            try:
                shutil.copy2(file_path, os.path.join(backup_dir, file_path))
                print(f"Backed up: {file_path}")
            except Exception as e:
                print(f"Error backing up {file_path}: {e}")

def update_code_snippets(code_snippet, description=None, category=None):
    """Add a code snippet to the code snippets file"""
    try:
        with open(CODE_SNIPPETS_FILE, 'r') as f:
            snippets_data = json.load(f)
    except:
        snippets_data = {"project": "Payymo Open Banking Integration", "snippets": {}}
    
    # Generate a unique ID for the snippet
    snippet_id = f"snippet_{len(snippets_data['snippets']) + 1}"
    
    # Add the snippet
    snippets_data["snippets"][snippet_id] = {
        "code": code_snippet,
        "description": description or "Code snippet",
        "category": category or "general",
        "added_at": datetime.datetime.now().isoformat()
    }
    
    # Save the updated snippets
    with open(CODE_SNIPPETS_FILE, 'w') as f:
        json.dump(snippets_data, f, indent=2)
    
    print(f"Added code snippet: {snippet_id}")

def cleanup_old_backups():
    """Maintain only the most recent MAX_BACKUPS backups per day"""
    for date_dir in os.listdir(BACKUP_DIR):
        date_path = os.path.join(BACKUP_DIR, date_dir)
        if os.path.isdir(date_path) and date_dir.startswith("20"):  # Only process date directories
            backups = sorted([d for d in os.listdir(date_path) if os.path.isdir(os.path.join(date_path, d))])
            if len(backups) > MAX_BACKUPS:
                for old_backup in backups[:-MAX_BACKUPS]:
                    try:
                        shutil.rmtree(os.path.join(date_path, old_backup))
                        print(f"Removed old backup: {date_dir}/{old_backup}")
                    except Exception as e:
                        print(f"Error removing old backup {date_dir}/{old_backup}: {e}")

def main():
    """Main function to run the backup process at regular intervals"""
    print(f"Starting backup service. Will save backups every {INTERVAL_SECONDS//60} minutes.")
    
    try:
        while True:
            backup_dir = create_backup()
            cleanup_old_backups()
            
            # Sleep until next backup
            print(f"Next backup in {INTERVAL_SECONDS//60} minutes. Press Ctrl+C to stop.")
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Backup service stopped by user.")
    except Exception as e:
        print(f"Error in backup service: {e}")

if __name__ == "__main__":
    main()