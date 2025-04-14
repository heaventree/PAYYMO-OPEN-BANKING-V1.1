#!/usr/bin/env python3
"""
Rollback to Approved Revision
This script provides an interactive way to roll back to a previously saved revision.
It presents a list of available revisions and allows you to choose one for rollback.

Usage:
  python rollback_to_approved.py [revision_id]
"""

import sys
import os
import subprocess
import json
from datetime import datetime

REVISIONS_DIR = "approved_revisions"

def get_available_revisions():
    """
    Get a list of all available revisions for rollback
    
    Returns:
        List of revision dictionaries
    """
    index_file = os.path.join(REVISIONS_DIR, "revisions_index.json")
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r') as f:
                index = json.load(f)
                return index["revisions"]
        except Exception as e:
            print(f"Error reading revisions index: {e}")
    return []

def display_revisions(revisions):
    """
    Display a list of available revisions
    
    Args:
        revisions: List of revision dictionaries
    """
    if not revisions:
        print("❌ No approved revisions found for rollback.")
        print("You need to create approved revisions first using save_approved.py")
        return
    
    print("\n📋 Available Approved Revisions:")
    print("===============================")
    for i, rev in enumerate(revisions):
        # Parse the date from the ISO format
        try:
            created_date = datetime.fromisoformat(rev['created_at']).strftime("%Y-%m-%d %H:%M:%S")
        except:
            created_date = rev['created_at']
            
        print(f"{i+1}. {rev['name']}")
        print(f"   ID: {rev['id']}")
        print(f"   Created: {created_date}")
        print(f"   Description: {rev['description']}")
        print()

def rollback_to_revision(revision_id):
    """
    Roll back to a specific revision
    
    Args:
        revision_id: ID of the revision to roll back to
        
    Returns:
        Success status (boolean)
    """
    try:
        # Call the backup script to roll back to the specified revision
        cmd = ["python", "backup_chat.py", "rollback", revision_id]
        
        print(f"⏪ Rolling back to revision: {revision_id}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully rolled back to revision: {revision_id}")
            return True
        else:
            print(f"❌ Failed to roll back: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error during rollback: {e}")
        return False

def interactive_rollback():
    """
    Interactive rollback process
    
    Returns:
        Success status (boolean)
    """
    revisions = get_available_revisions()
    display_revisions(revisions)
    
    if not revisions:
        return False
    
    try:
        choice = input("Enter the number of the revision to roll back to (or 'q' to quit): ")
        
        if choice.lower() == 'q':
            print("Rollback cancelled.")
            return False
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(revisions):
                revision_id = revisions[index]['id']
                confirm = input(f"Are you sure you want to roll back to '{revisions[index]['name']}'? (y/n): ")
                
                if confirm.lower() == 'y':
                    return rollback_to_revision(revision_id)
                else:
                    print("Rollback cancelled.")
                    return False
            else:
                print("Invalid selection.")
                return False
        except ValueError:
            print("Please enter a valid number.")
            return False
    except KeyboardInterrupt:
        print("\nRollback cancelled.")
        return False

def main():
    """Main function to process command line arguments and perform rollback"""
    if len(sys.argv) > 1:
        # Direct rollback to specified revision ID
        revision_id = sys.argv[1]
        rollback_to_revision(revision_id)
    else:
        # Interactive rollback
        interactive_rollback()

if __name__ == "__main__":
    main()