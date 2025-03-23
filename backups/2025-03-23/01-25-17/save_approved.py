#!/usr/bin/env python3
"""
Save Approved Revision
This script creates a snapshot of the current project state, specifically for
approved pages that need to be preserved for potential rollback.

Usage:
  python save_approved.py "Dashboard Layout" "Final approved version of dashboard layout with filters in header"
"""

import sys
import os
import subprocess
from datetime import datetime

def save_approved_revision(name=None, description=None):
    """
    Save the current state as an approved revision using the backup script
    
    Args:
        name: Optional name for this approved revision
        description: Optional description of the revision
    """
    # Default name and description if not provided
    if not name:
        name = f"Approved_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not description:
        description = "Approved page/feature revision"
    
    # Add timestamp to name if not already present
    if not any(c.isdigit() for c in name):
        name = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    try:
        # Call the backup script to create a new revision
        cmd = ["python", "backup_chat.py", "revision", 
               "-n", name, 
               "-d", description]
        
        print(f"Creating approved revision: {name}")
        print(f"Description: {description}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully saved approved revision: {name}")
            print("\nAvailable revisions for rollback:")
            # List available revisions
            list_cmd = ["python", "backup_chat.py", "list"]
            subprocess.run(list_cmd)
            return True
        else:
            print(f"❌ Failed to save revision: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error saving revision: {e}")
        return False

def main():
    """Main function to process command line arguments and save revision"""
    if len(sys.argv) > 1:
        name = sys.argv[1]
        description = sys.argv[2] if len(sys.argv) > 2 else None
        save_approved_revision(name, description)
    else:
        print("Usage: python save_approved.py \"Revision Name\" \"Revision Description\"")
        print("\nCreating a default approved revision...")
        save_approved_revision()

if __name__ == "__main__":
    main()