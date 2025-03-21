#!/usr/bin/env python3
"""
Backup chat script that saves conversation to JSON files every 15 minutes.
Run in the background with: nohup python3 backup_chat.py &
"""

import json
import os
import time
import datetime
import shutil
from pathlib import Path

# Configuration
BACKUP_DIR = "backups/chat"
INTERVAL_SECONDS = 15 * 60  # 15 minutes
MAX_BACKUPS = 10  # Keep last 10 backups

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup():
    """Create a backup of the current chat state"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_DIR, f"chat_backup_{timestamp}.json")
    
    # This is a placeholder for actual chat data collection
    # In a real implementation, this would extract data from the chat system
    chat_data = {
        "timestamp": timestamp,
        "metadata": {
            "backup_time": datetime.datetime.now().isoformat(),
            "project": "Payymo Open Banking Integration",
        },
        "messages": [
            # This would be populated with actual chat messages
            {"role": "system", "content": "This is a backup of the chat session."},
            {"role": "user", "content": "Placeholder for actual chat content"},
            {"role": "assistant", "content": "Placeholder for actual responses"},
        ],
        "codefiles": {},
    }
    
    # Also back up key files
    backup_files(chat_data, timestamp)
    
    # Save to JSON file
    with open(backup_file, 'w') as f:
        json.dump(chat_data, f, indent=2)
    
    print(f"Backup created: {backup_file}")
    return backup_file

def backup_files(chat_data, timestamp):
    """Add key project files to the backup"""
    key_directories = [
        "flask_backend/templates/components",
        "flask_backend/static/js",
        "flask_backend/static/css",
    ]
    
    for directory in key_directories:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            chat_data["codefiles"][filepath] = content
                    except Exception as e:
                        print(f"Error backing up {filepath}: {e}")

def cleanup_old_backups():
    """Maintain only the most recent MAX_BACKUPS backups"""
    backups = sorted(Path(BACKUP_DIR).glob("chat_backup_*.json"))
    if len(backups) > MAX_BACKUPS:
        for old_backup in backups[:-MAX_BACKUPS]:
            try:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")
            except Exception as e:
                print(f"Error removing old backup {old_backup}: {e}")

def main():
    """Main function to run the backup process at regular intervals"""
    print(f"Starting chat backup service. Will save backups every {INTERVAL_SECONDS//60} minutes.")
    
    try:
        while True:
            backup_file = create_backup()
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