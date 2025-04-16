#!/usr/bin/env python3
"""
Simple Backup Service for Payymo
Runs as a continuous service, creating backups every 15 minutes.
Designed to be robust and easy to monitor.

Usage:
  python simple_backup_service.py start  # Start the service
  python simple_backup_service.py stop   # Stop the service
  python simple_backup_service.py status # Show service status
  python simple_backup_service.py once   # Run one backup cycle and exit
"""

import os
import sys
import time
import datetime
import signal
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_backup_service")

# Constants
PID_FILE = "backup_service.pid"
INTERVAL_SECONDS = 15 * 60  # 15 minutes
BACKUP_COMMANDS = [
    ["python", "backup_chat.py", "backup"],
    ["python", "backup_chat.py", "chat"]
]

def write_pid():
    """Write our PID to the PID file"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    os.chmod(PID_FILE, 0o644)
    logger.info(f"PID file created: {os.getpid()}")

def read_pid():
    """Read the PID from the PID file"""
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def is_running(pid=None):
    """Check if the backup service is running"""
    if pid is None:
        pid = read_pid()
    
    if pid is None:
        return False
        
    try:
        # This will raise an exception if the process is not running
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False

def stop_service():
    """Stop the backup service"""
    pid = read_pid()
    if pid is None:
        logger.info("No PID file found. Service not running or PID file missing.")
        return False
    
    if not is_running(pid):
        logger.info(f"Process with PID {pid} is not running. Cleaning up PID file.")
        os.remove(PID_FILE)
        return False
    
    logger.info(f"Stopping backup service (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait for the process to terminate
        for _ in range(10):
            time.sleep(0.5)
            if not is_running(pid):
                logger.info(f"Service stopped successfully.")
                return True
        
        # If still running, force kill
        os.kill(pid, signal.SIGKILL)
        logger.info(f"Service had to be force killed.")
        return True
    except (ProcessLookupError, PermissionError):
        logger.info(f"Process already stopped.")
        return False
    finally:
        # Always try to clean up the PID file
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass

def run_backup_commands():
    """Run all the backup commands"""
    all_successful = True
    
    for command in BACKUP_COMMANDS:
        logger.info(f"Running: {' '.join(command)}")
        start_time = time.time()
        
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Command successful: {' '.join(command)}")
            else:
                logger.error(f"Command failed: {' '.join(command)}")
                logger.error(f"Error: {result.stderr.strip()}")
                all_successful = False
        except Exception as e:
            logger.error(f"Exception running command: {' '.join(command)}")
            logger.error(f"Error: {str(e)}")
            all_successful = False
        
        elapsed = time.time() - start_time
        logger.info(f"Command took {elapsed:.2f} seconds")
    
    # Also let's create an initial revision once a day
    if datetime.datetime.now().hour == 0 and datetime.datetime.now().minute < 15:
        logger.info("Creating daily revision snapshot")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            subprocess.run(
                ["python", "save_approved.py", f"Daily Backup {date_str}", "Automatic daily snapshot"], 
                capture_output=True, 
                text=True
            )
            logger.info("Daily revision created successfully")
        except Exception as e:
            logger.error(f"Error creating daily revision: {str(e)}")
            all_successful = False
    
    return all_successful

def run_service():
    """Run the backup service in a loop"""
    logger.info(f"Starting backup service (PID: {os.getpid()})...")
    logger.info(f"Will create backups every {INTERVAL_SECONDS // 60} minutes")
    
    write_pid()
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}. Stopping...")
        try:
            os.remove(PID_FILE)
        except:
            pass
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run first backup immediately
    run_backup_commands()
    
    last_run = time.time()
    failures = 0
    
    try:
        while True:
            # Check if the PID file still exists and contains our PID
            if not os.path.exists(PID_FILE):
                logger.info("PID file has been removed. Exiting...")
                break
            
            current_pid = read_pid()
            if current_pid != os.getpid():
                logger.info(f"PID file contains different PID: {current_pid}. Exiting...")
                break
            
            # Calculate time to next backup
            now = time.time()
            elapsed = now - last_run
            remaining = max(0, INTERVAL_SECONDS - elapsed)
            
            if remaining == 0:
                logger.info("Time for next backup cycle...")
                success = run_backup_commands()
                last_run = time.time()
                
                if not success:
                    failures += 1
                    logger.warning(f"Backup cycle had errors ({failures} failures so far)")
                else:
                    failures = 0
                    logger.info("Backup cycle completed successfully")
                
                # If too many consecutive failures, give up
                if failures >= 3:
                    logger.error("Too many consecutive failures. Exiting...")
                    break
            else:
                # Sleep for 1 minute or the remaining time, whichever is shorter
                sleep_time = min(60, remaining)
                time.sleep(sleep_time)
    except Exception as e:
        logger.error(f"Error in backup service: {str(e)}")
    finally:
        # Clean up
        try:
            os.remove(PID_FILE)
        except:
            pass
        logger.info("Backup service stopped")

def show_status():
    """Show the status of the backup service"""
    pid = read_pid()
    if pid is None:
        print("❌ Backup service is NOT RUNNING")
        print(f"To start: python {sys.argv[0]} start")
        return
    
    if is_running(pid):
        print(f"✅ Backup service is RUNNING (PID: {pid})")
        
        # Get process start time
        try:
            result = subprocess.run(['ps', '-p', str(pid), '-o', 'start,cmd'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"   Started: {lines[1].split()[0]}")
        except:
            pass
        
        # Get log file info
        log_file = "backup_system.log"
        if os.path.exists(log_file):
            log_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
            now = datetime.datetime.now()
            delta = now - log_mtime
            minutes_ago = delta.total_seconds() / 60
            
            print(f"   Last log update: {minutes_ago:.1f} minutes ago")
            
            # Estimate time to next backup
            if minutes_ago < INTERVAL_SECONDS / 60:
                next_backup = INTERVAL_SECONDS / 60 - minutes_ago
                print(f"   Next backup in approximately {next_backup:.1f} minutes")
            
            # Show recent log entries
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-5:] if len(lines) > 5 else lines
                    
                    print("\nRecent log entries:")
                    for line in last_lines:
                        print(f"   {line.strip()}")
            except Exception as e:
                print(f"Error reading log file: {e}")
    else:
        print(f"❌ Backup service is NOT RUNNING (stale PID file found)")
        print(f"To clean up and start: python {sys.argv[0]} start")
        try:
            os.remove(PID_FILE)
            print("   Removed stale PID file.")
        except:
            pass

def run_once():
    """Run one backup cycle and exit"""
    logger.info("Running single backup cycle...")
    success = run_backup_commands()
    if success:
        logger.info("Backup cycle completed successfully")
        return True
    else:
        logger.error("Backup cycle had errors")
        return False

def main():
    """Main function to parse command line arguments and take action"""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} [start|stop|status|once]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        # Check if already running
        if is_running():
            print(f"Backup service is already running.")
            return
        
        # Clean up stale PID file if it exists
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        
        # Fork a child process to run the service
        if os.fork() == 0:
            # This is the child process
            # Detach from terminal
            os.setsid()
            
            # Close file descriptors
            os.close(0)
            os.close(1)
            os.close(2)
            
            # Run the service
            run_service()
            sys.exit(0)
        else:
            # This is the parent process
            print(f"Backup service started in the background.")
            # Wait a bit for the child to create the PID file
            time.sleep(1)
            if os.path.exists(PID_FILE):
                print(f"PID file created: {read_pid()}")
                print(f"To check status: python {sys.argv[0]} status")
                print(f"To stop: python {sys.argv[0]} stop")
            else:
                print(f"Warning: PID file not created yet. Service may have failed to start.")
    
    elif command == "stop":
        if stop_service():
            print("Backup service stopped.")
        else:
            print("No running backup service found.")
    
    elif command == "status":
        show_status()
    
    elif command == "once":
        print("Running one backup cycle...")
        success = run_once()
        if success:
            print("Backup cycle completed successfully.")
        else:
            print("Backup cycle had errors. Check the logs for details.")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        print(f"Usage: python {sys.argv[0]} [start|stop|status|once]")

if __name__ == "__main__":
    main()