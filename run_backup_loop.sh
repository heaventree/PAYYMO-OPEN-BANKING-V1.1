#!/bin/bash
# Backup loop script that runs the backup every 15 minutes
# Run in the background with: nohup bash run_backup_loop.sh &

echo "Starting Payymo backup system..."
echo "Backups will run every 15 minutes"
echo "Started at $(date)"

# Create initial backup and revision
python backup_chat.py backup
python save_approved.py "Initial Backup" "Initial state for the backup system"

# Log file for the backup process
LOGFILE="backup_system.log"

# Run forever
while true; do
    echo "$(date): Running backup..." >> $LOGFILE
    
    # Run the backup
    python backup_chat.py backup >> $LOGFILE 2>&1
    
    # Back up chat history
    python backup_chat.py chat >> $LOGFILE 2>&1
    
    echo "$(date): Backup complete. Next backup in 15 minutes." >> $LOGFILE
    
    # Wait for 15 minutes (900 seconds)
    sleep 900
done