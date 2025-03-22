#!/usr/bin/env python3
"""
Enhanced Backup & Revision System
Saves conversation history, code snippets, and file changes every 15 minutes.
Also maintains a separate approved revisions folder for immediate rollback.

Run in the background with: nohup python3 backup_chat.py &
"""

import json
import os
import re
import sys
import time
import datetime
import shutil
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backup_system")

# Configuration
BACKUP_DIR = "backups"  # Internal backups
GITHUB_BACKUP_DIR = "github_ready_backups"  # GitHub-ready backups
REVISIONS_DIR = "approved_revisions"  # Approved revisions for rollback
CHAT_HISTORY_DIR = "chat_history"  # Chat history archives
CODE_SNIPPETS_FILE = os.path.join(GITHUB_BACKUP_DIR, "code_snippets.json")
INTERVAL_SECONDS = 15 * 60  # 15 minutes (900 seconds)
MAX_BACKUPS = 10  # Keep last 10 backups per day
MAX_REVISIONS = 5  # Keep last 5 approved revisions

# Important files to always include in backups
KEY_FILES = [
    # Core application files
    "main.py",
    "flask_backend/app.py",
    "flask_backend/routes.py",
    "flask_backend/models.py",
    
    # Service modules
    "flask_backend/services/gocardless_service.py",
    "flask_backend/services/invoice_matching_service.py",
    "flask_backend/services/stripe_service.py",
    "flask_backend/services/license_service.py",
    
    # Frontend assets (JS/CSS)
    "flask_backend/static/js/main.js",
    "flask_backend/static/js/bank_wizard.js",
    "flask_backend/static/js/stripe_wizard.js",
    "flask_backend/static/js/quick_insights.js",
    "flask_backend/static/js/onboarding_walkthrough.js",
    "flask_backend/static/css/style.css",
    
    # Templates
    "flask_backend/templates/dashboard.html",
    "flask_backend/templates/components/bank_connection_wizard.html",
    "flask_backend/templates/components/stripe_connection_wizard.html",
    "flask_backend/templates/components/financial_goals.html",
    "flask_backend/templates/components/feature_card_template.html",
    
    # Documentation
    "flask_backend/ui_standards.md",
    "flask_backend/UI_DEVELOPER_README.md",
    
    # Utils
    "flask_backend/utils/db.py",
    "flask_backend/utils/error_handler.py",
    "flask_backend/utils/logger.py",
    
    # Script files
    "backup_chat.py",
    "save_approved.py",
    "rollback_to_approved.py",
    "add_test_data.py",
]

# Ensure all backup directories exist
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(GITHUB_BACKUP_DIR, exist_ok=True)
os.makedirs(REVISIONS_DIR, exist_ok=True)
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

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

def backup_chat_history():
    """Backup chat history from the system logs"""
    try:
        # Use a timestamp for the chat history backup
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        chat_backup_file = os.path.join(CHAT_HISTORY_DIR, f"chat_history_{timestamp}.json")
        
        # Here we would extract the chat history from the system
        # This is a placeholder - the actual implementation would depend on how chat data is stored
        chat_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "messages": [],  # This would be populated with actual chat messages
            "metadata": {
                "backup_id": timestamp,
                "project": "Payymo Open Banking Integration"
            }
        }
        
        # Save the chat history
        with open(chat_backup_file, 'w') as f:
            json.dump(chat_data, f, indent=2)
        
        logger.info(f"Chat history backed up to: {chat_backup_file}")
        return chat_backup_file
    except Exception as e:
        logger.error(f"Error backing up chat history: {e}")
        return None

def create_revision(name=None, description=None):
    """
    Create a new revision snapshot of the current state
    This is for approved pages/states that need to be available for rollback
    
    Args:
        name: Optional name for this revision
        description: Optional description of what this revision represents
    
    Returns:
        Path to the revision directory
    """
    try:
        # Generate a unique revision ID with timestamp and optional name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if name:
            revision_id = f"{timestamp}_{name.replace(' ', '_')}"
        else:
            revision_id = timestamp
        
        revision_dir = os.path.join(REVISIONS_DIR, revision_id)
        os.makedirs(revision_dir, exist_ok=True)
        
        # Backup all key files to the revision directory
        for file_path in KEY_FILES:
            if os.path.exists(file_path):
                # Create the directory structure
                target_path = os.path.join(revision_dir, os.path.dirname(file_path))
                os.makedirs(target_path, exist_ok=True)
                
                # Copy the file
                try:
                    shutil.copy2(file_path, os.path.join(revision_dir, file_path))
                except Exception as e:
                    logger.error(f"Error saving file to revision {file_path}: {e}")
        
        # Create a revision info file
        info_file = os.path.join(revision_dir, "revision_info.json")
        revision_info = {
            "id": revision_id,
            "name": name or f"Revision {timestamp}",
            "description": description or "Automatic revision snapshot",
            "created_at": datetime.datetime.now().isoformat(),
            "files": [f for f in KEY_FILES if os.path.exists(os.path.join(revision_dir, f))]
        }
        
        with open(info_file, 'w') as f:
            json.dump(revision_info, f, indent=2)
        
        # Create or update the revisions index
        index_file = os.path.join(REVISIONS_DIR, "revisions_index.json")
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                try:
                    index = json.load(f)
                except:
                    index = {"revisions": []}
        else:
            index = {"revisions": []}
        
        # Add the new revision to the index
        index["revisions"].append({
            "id": revision_id,
            "name": name or f"Revision {timestamp}",
            "description": description or "Automatic revision snapshot",
            "created_at": datetime.datetime.now().isoformat()
        })
        
        # Sort revisions by creation time (newest first)
        index["revisions"] = sorted(
            index["revisions"], 
            key=lambda x: x["created_at"], 
            reverse=True
        )
        
        # Limit to MAX_REVISIONS
        if len(index["revisions"]) > MAX_REVISIONS:
            # Get the IDs of revisions to delete
            to_delete = index["revisions"][MAX_REVISIONS:]
            index["revisions"] = index["revisions"][:MAX_REVISIONS]
            
            # Delete old revision directories
            for revision in to_delete:
                old_dir = os.path.join(REVISIONS_DIR, revision["id"])
                if os.path.exists(old_dir):
                    try:
                        shutil.rmtree(old_dir)
                        logger.info(f"Removed old revision: {revision['id']}")
                    except Exception as e:
                        logger.error(f"Error removing old revision {revision['id']}: {e}")
        
        # Save the updated index
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        logger.info(f"Created revision snapshot: {revision_id}")
        return revision_dir
    except Exception as e:
        logger.error(f"Error creating revision: {e}")
        return None

def rollback_to_revision(revision_id):
    """
    Roll back to a specific revision
    
    Args:
        revision_id: ID of the revision to roll back to
        
    Returns:
        Success status (boolean)
    """
    try:
        revision_dir = os.path.join(REVISIONS_DIR, revision_id)
        if not os.path.exists(revision_dir):
            logger.error(f"Revision not found: {revision_id}")
            return False
        
        # First create a backup of the current state
        backup_dir = create_backup()
        logger.info(f"Created pre-rollback backup: {backup_dir}")
        
        # Restore files from the revision
        for file_path in KEY_FILES:
            revision_file = os.path.join(revision_dir, file_path)
            if os.path.exists(revision_file):
                # Ensure the target directory exists
                target_dir = os.path.dirname(file_path)
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy the file from revision to the current directory
                try:
                    shutil.copy2(revision_file, file_path)
                    logger.info(f"Restored file: {file_path}")
                except Exception as e:
                    logger.error(f"Error restoring file {file_path}: {e}")
        
        logger.info(f"Successfully rolled back to revision: {revision_id}")
        return True
    except Exception as e:
        logger.error(f"Error rolling back to revision {revision_id}: {e}")
        return False

def list_available_revisions():
    """
    List all available revisions for rollback
    
    Returns:
        List of revision information dictionaries
    """
    index_file = os.path.join(REVISIONS_DIR, "revisions_index.json")
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r') as f:
                index = json.load(f)
                return index["revisions"]
        except Exception as e:
            logger.error(f"Error reading revisions index: {e}")
    return []

def main():
    """Main function to run the backup process at regular intervals"""
    # Create PID file to track the service
    pid = os.getpid()
    with open("backup_pid.txt", "w") as f:
        f.write(str(pid))
    
    logger.info(f"Starting backup service (PID: {pid}). Will save backups every {INTERVAL_SECONDS//60} minutes.")
    
    # Create an initial backup and revision
    try:
        initial_backup_dir = create_backup()
        logger.info(f"Created initial backup: {initial_backup_dir}")
        
        initial_revision = create_revision("initial_state", "Initial project state at backup service start")
        logger.info(f"Created initial revision: {initial_revision}")
        
        backup_chat_history()
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
    
    try:
        # Register signal handlers for better cleanup
        import signal
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}. Stopping backup service.")
            try:
                os.remove("backup_pid.txt")
            except:
                pass
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while True:
            try:
                # Check if we should still be running
                if not os.path.exists("backup_pid.txt"):
                    logger.info("PID file removed. Stopping backup service.")
                    break
                
                backup_dir = create_backup()
                logger.info(f"Created backup: {backup_dir}")
                
                chat_backup = backup_chat_history()
                logger.info(f"Backed up chat history: {chat_backup}")
                
                cleanup_old_backups()
            except Exception as e:
                logger.error(f"Error during backup cycle: {e}")
            
            # Sleep until next backup
            logger.info(f"Next backup in {INTERVAL_SECONDS//60} minutes.")
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("Backup service stopped by user.")
    except Exception as e:
        logger.error(f"Error in backup service: {e}")
    
    # Clean up PID file
    try:
        os.remove("backup_pid.txt")
    except:
        pass

def parse_args():
    """Parse command line arguments for the backup tool"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Payymo Backup and Revision System")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start the backup service
    start_parser = subparsers.add_parser("start", help="Start the backup service")
    
    # Create a new revision
    revision_parser = subparsers.add_parser("revision", help="Create a new revision snapshot")
    revision_parser.add_argument("-n", "--name", help="Name for this revision")
    revision_parser.add_argument("-d", "--description", help="Description of this revision")
    
    # List all available revisions
    list_parser = subparsers.add_parser("list", help="List all available revisions")
    
    # Roll back to a specific revision
    rollback_parser = subparsers.add_parser("rollback", help="Roll back to a specific revision")
    rollback_parser.add_argument("revision_id", help="ID of the revision to roll back to")
    
    # Backup the current state now
    backup_parser = subparsers.add_parser("backup", help="Create a backup of the current state")
    
    # Backup chat history
    chat_parser = subparsers.add_parser("chat", help="Backup chat history")
    
    # Create GitHub-ready backup
    github_parser = subparsers.add_parser("github", help="Create a GitHub-ready backup of core files")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.command == "start" or args.command is None:
        main()
    elif args.command == "revision":
        create_revision(args.name, args.description)
    elif args.command == "list":
        revisions = list_available_revisions()
        if revisions:
            print("\nAvailable Revisions:")
            print("====================")
            for i, rev in enumerate(revisions):
                print(f"{i+1}. {rev['name']} (ID: {rev['id']})")
                print(f"   Created: {rev['created_at']}")
                print(f"   Description: {rev['description']}")
                print()
        else:
            print("No revisions available.")
    elif args.command == "rollback":
        success = rollback_to_revision(args.revision_id)
        if success:
            print(f"Successfully rolled back to revision: {args.revision_id}")
        else:
            print(f"Failed to roll back to revision: {args.revision_id}")
    elif args.command == "backup":
        backup_dir = create_backup()
        print(f"Backup created: {backup_dir}")
    elif args.command == "chat":
        chat_file = backup_chat_history()
        print(f"Chat history backed up to: {chat_file}")
    elif args.command == "github":
        github_dir = create_github_backup()
        print(f"GitHub-ready backup created at: {github_dir}")
    else:
        main()