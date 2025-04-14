#!/bin/bash
# Enhanced backup loop script that runs backups every 15 minutes
# Run in the background with: nohup bash run_backup_loop.sh > backup_runner.log 2>&1 &

# Make this script immune to hangup signal
set -m  # Enable job control
trap '' HUP  # Ignore hangup signals

# Store our own PID for tracking
SCRIPT_PID=$$
echo $SCRIPT_PID > backup_runner_pid.txt
chmod 644 backup_runner_pid.txt

# Log file for the backup process
LOGFILE="backup_system.log"

echo "===============================================" | tee -a $LOGFILE
echo "Starting Payymo backup system (PID: $SCRIPT_PID)..." | tee -a $LOGFILE
echo "Backups will run every 15 minutes" | tee -a $LOGFILE
echo "Started at $(date)" | tee -a $LOGFILE
echo "===============================================" | tee -a $LOGFILE

# Function to clean up when exiting
cleanup() {
    echo "$(date): Stopping backup system (PID: $SCRIPT_PID)..." | tee -a $LOGFILE
    # Remove PID file if it's our PID
    if [ -f "backup_runner_pid.txt" ]; then
        STORED_PID=$(cat backup_runner_pid.txt)
        if [ "$STORED_PID" = "$SCRIPT_PID" ]; then
            rm backup_runner_pid.txt
            echo "$(date): Removed PID file." | tee -a $LOGFILE
        fi
    fi
    # Also clean up the backup_pid.txt file used by Python script
    if [ -f "backup_pid.txt" ]; then
        rm backup_pid.txt
        echo "$(date): Removed Python PID file." | tee -a $LOGFILE
    fi
    echo "$(date): Backup system stopped." | tee -a $LOGFILE
    exit 0
}

# Set up trap for signals
trap cleanup SIGINT SIGTERM EXIT

# Create initial backup and revision
echo "$(date): Creating initial backup..." | tee -a $LOGFILE
python backup_chat.py backup >> $LOGFILE 2>&1
echo "$(date): Creating initial revision..." | tee -a $LOGFILE
python save_approved.py "Initial Backup" "Initial state for the backup system" >> $LOGFILE 2>&1
echo "$(date): Backing up chat history..." | tee -a $LOGFILE
python backup_chat.py chat >> $LOGFILE 2>&1

# Log start of continuous backup loop
echo "$(date): Starting continuous backup loop..." | tee -a $LOGFILE

# Run forever
while true; do
    # Check if we should still be running
    if [ ! -f "backup_runner_pid.txt" ]; then
        echo "$(date): PID file removed. Stopping backup system." | tee -a $LOGFILE
        exit 0
    fi
    
    # Check if correct PID is in the file
    if [ -f "backup_runner_pid.txt" ]; then
        STORED_PID=$(cat backup_runner_pid.txt)
        if [ "$STORED_PID" != "$SCRIPT_PID" ]; then
            echo "$(date): PID mismatch (stored: $STORED_PID, actual: $SCRIPT_PID). Stopping backup system." | tee -a $LOGFILE
            exit 0
        fi
    fi
    
    # Run the backup
    echo "$(date): Running backup cycle..." | tee -a $LOGFILE
    
    # Create backup
    echo "$(date): Creating backup..." | tee -a $LOGFILE
    python backup_chat.py backup >> $LOGFILE 2>&1
    
    # Back up chat history
    echo "$(date): Backing up chat history..." | tee -a $LOGFILE
    python backup_chat.py chat >> $LOGFILE 2>&1
    
    echo "$(date): Backup cycle complete. Next backup in 15 minutes." | tee -a $LOGFILE
    
    # Wait for 15 minutes (900 seconds)
    # We'll check every minute if we should still be running
    for ((i=1; i<=15; i++)); do
        sleep 60
        # Check if we should stop
        if [ ! -f "backup_runner_pid.txt" ]; then
            echo "$(date): PID file removed. Stopping backup system." | tee -a $LOGFILE
            exit 0
        fi
    done
done