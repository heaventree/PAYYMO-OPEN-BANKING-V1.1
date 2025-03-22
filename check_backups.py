#!/usr/bin/env python3
"""
Check Backup System Status
This utility script displays the status of the backup system, including:
- Recent backups
- Available revisions for rollback
- Backup service status
- Chat history backups
"""

import os
import sys
import time
import json
import datetime
import subprocess

# Configuration
BACKUP_DIR = "backups"
GITHUB_BACKUP_DIR = "github_ready_backups"
REVISIONS_DIR = "approved_revisions"
CHAT_HISTORY_DIR = "chat_history"
LOG_FILE = "backup_system.log"

def format_time_ago(timestamp_str):
    """Format a timestamp as a human-readable time ago string"""
    try:
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except:
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            return timestamp_str
    
    now = datetime.datetime.now()
    delta = now - timestamp
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    minutes = (delta.seconds % 3600) // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "Just now"

def check_backups():
    """Check and display information about recent backups"""
    print("\n📂 RECENT BACKUPS")
    print("==============")
    
    if not os.path.exists(BACKUP_DIR):
        print("No backups found. Backup system may not be initialized.")
        return
    
    # Get the date directories
    date_dirs = sorted([d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))], reverse=True)
    
    if not date_dirs:
        print("No backups found.")
        return
    
    total_backups = 0
    
    # Show the most recent few days of backups
    for date_dir in date_dirs[:3]:
        backup_time_dirs = sorted([d for d in os.listdir(os.path.join(BACKUP_DIR, date_dir)) 
                                  if os.path.isdir(os.path.join(BACKUP_DIR, date_dir, d))], reverse=True)
        
        if backup_time_dirs:
            print(f"\n📅 {date_dir}:")
            for time_dir in backup_time_dirs[:5]:  # Show the 5 most recent backups for each day
                backup_path = os.path.join(BACKUP_DIR, date_dir, time_dir)
                backup_info_path = os.path.join(backup_path, "backup_info.txt")
                
                backup_time = time_dir.replace('-', ':')
                if os.path.exists(backup_info_path):
                    file_count = sum(len(files) for _, _, files in os.walk(backup_path)) - 1  # Exclude backup_info.txt
                    size_kb = sum(os.path.getsize(os.path.join(root, file)) for root, _, files in os.walk(backup_path) 
                                 for file in files) / 1024
                    
                    # Get creation time
                    created_time = datetime.datetime.fromtimestamp(os.path.getctime(backup_path))
                    time_ago = format_time_ago(created_time.isoformat())
                    
                    print(f"  ⏱️ {backup_time} ({time_ago}) - {file_count} files, {size_kb:.1f} KB")
                else:
                    print(f"  ⏱️ {backup_time}")
                
                total_backups += 1
        
        # If we have enough total backups, stop
        if total_backups >= 10:
            break
    
    # Show total backup stats
    total_days = len(date_dirs)
    all_backups = sum(len([d for d in os.listdir(os.path.join(BACKUP_DIR, date_dir)) 
                         if os.path.isdir(os.path.join(BACKUP_DIR, date_dir, d))]) 
                     for date_dir in date_dirs)
    
    print(f"\nTotal: {all_backups} backups across {total_days} days")

def check_revisions():
    """Check and display information about available revisions"""
    print("\n🔄 AVAILABLE REVISIONS FOR ROLLBACK")
    print("===============================")
    
    if not os.path.exists(REVISIONS_DIR):
        print("No revisions found. Revision system may not be initialized.")
        return
    
    index_file = os.path.join(REVISIONS_DIR, "revisions_index.json")
    if not os.path.exists(index_file):
        print("No revisions index found.")
        return
    
    try:
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        if not index.get("revisions"):
            print("No revisions available.")
            return
        
        for i, rev in enumerate(index["revisions"]):
            try:
                created_date = datetime.datetime.fromisoformat(rev['created_at'])
                time_ago = format_time_ago(rev['created_at'])
                date_str = created_date.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = rev.get('created_at', 'Unknown')
                time_ago = "Unknown"
            
            print(f"{i+1}. {rev.get('name', 'Unnamed')} ({time_ago})")
            print(f"   ID: {rev.get('id', 'Unknown')}")
            print(f"   Created: {date_str}")
            print(f"   Description: {rev.get('description', 'No description')}")
            print()
    except Exception as e:
        print(f"Error reading revisions index: {e}")

def check_chat_history():
    """Check and display information about chat history backups"""
    print("\n💬 CHAT HISTORY BACKUPS")
    print("====================")
    
    if not os.path.exists(CHAT_HISTORY_DIR):
        print("No chat history backups found. Chat backup system may not be initialized.")
        return
    
    chat_files = sorted([f for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith('.json')], reverse=True)
    
    if not chat_files:
        print("No chat history backups found.")
        return
    
    print(f"Found {len(chat_files)} chat history backups.")
    
    for i, chat_file in enumerate(chat_files[:5]):  # Show 5 most recent
        file_path = os.path.join(CHAT_HISTORY_DIR, chat_file)
        
        # Get file creation time
        created_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
        time_ago = format_time_ago(created_time.isoformat())
        
        # Get file size
        size_kb = os.path.getsize(file_path) / 1024
        
        # Try to get message count from the file
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                message_count = len(data.get("messages", []))
                timestamp = data.get("timestamp", "Unknown")
                
                print(f"{i+1}. {chat_file} ({time_ago})")
                print(f"   Timestamp: {timestamp}")
                print(f"   Size: {size_kb:.1f} KB")
                print(f"   Messages: {message_count}")
                print()
        except:
            print(f"{i+1}. {chat_file} ({time_ago})")
            print(f"   Size: {size_kb:.1f} KB")
            print()

def check_backup_service():
    """Check if the backup service is running"""
    print("\n🔄 BACKUP SERVICE STATUS")
    print("=====================")
    
    pid_file = "backup_pid.txt"
    
    try:
        # First check if we have a PID file
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            
            # Check if the process is actually running
            try:
                # This will raise an exception if the process is not running
                os.kill(int(pid), 0)
                print(f"✅ Backup service is RUNNING (PID: {pid})")
                
                # Get process info
                result = subprocess.run(['ps', '-p', pid, '-o', 'start,cmd'], capture_output=True, text=True)
                output = result.stdout
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    print(f"   Started: {lines[1].split()[0]}")
                    print(f"   Command: python backup_chat.py start")
            except (ProcessLookupError, PermissionError):
                print("❌ Backup service is NOT RUNNING (stale PID file found)")
                print("   To start it, run: nohup python backup_chat.py start > backup_runner.log 2>&1 &")
        else:
            # Check for any running python backup processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            output = result.stdout
            
            backup_processes = [line for line in output.split('\n') if 'python' in line and 'backup_chat.py' in line and 'start' in line and 'grep' not in line]
            
            if backup_processes:
                print("✅ Backup service is RUNNING (no PID file)")
                for proc in backup_processes:
                    parts = proc.split()
                    if len(parts) > 9:
                        pid = parts[1]
                        start_time = parts[9]
                        print(f"   PID: {pid}, Start time: {start_time}")
                print("   (Creating new PID file for tracking)")
                # Create PID file for the first process found
                if len(backup_processes) > 0:
                    parts = backup_processes[0].split()
                    if len(parts) > 1:
                        with open(pid_file, 'w') as f:
                            f.write(parts[1])
            else:
                print("❌ Backup service is NOT RUNNING")
                print("   To start it, run: nohup python backup_chat.py start > backup_runner.log 2>&1 &")
        
        # Check for recent activity in the log file
        if os.path.exists(LOG_FILE):
            log_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
            time_ago = format_time_ago(log_mtime.isoformat())
            print(f"\nLog file last updated: {time_ago}")
            
            # Show the last few lines of the log
            try:
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:] if len(lines) > 5 else lines
                    
                    print("\nRecent log entries:")
                    for line in last_lines:
                        print(f"   {line.strip()}")
            except Exception as e:
                print(f"Error reading log file: {e}")
        else:
            print("\nNo log file found.")
    except Exception as e:
        print(f"Error checking backup service status: {e}")

def main():
    """Main function to check backup system status"""
    print("\n===================================")
    print("📊 PAYYMO BACKUP SYSTEM STATUS 📊")
    print("===================================")
    
    check_backup_service()
    check_backups()
    check_revisions()
    check_chat_history()
    
    print("\n===================================")
    
    # Display helpful commands
    print("\n📋 USEFUL COMMANDS:")
    print("================")
    print("▶️ Start backup service:      nohup bash run_backup_loop.sh > backup_runner.log 2>&1 &")
    print("📦 Create backup now:         python backup_chat.py backup")
    print("💾 Save approved revision:    python save_approved.py \"Name\" \"Description\"")
    print("⏪ Rollback to a revision:    python rollback_to_approved.py")
    print("📜 View backup logs:          cat backup_system.log")
    print("🔍 Check backup status:       python check_backups.py")

if __name__ == "__main__":
    main()