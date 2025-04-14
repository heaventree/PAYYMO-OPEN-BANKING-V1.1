#!/usr/bin/env python3
"""
GoCardless Open Banking Transaction Fetcher

This script fetches transactions from GoCardless Open Banking API
for all active bank connections. It is designed to be run as a cron job.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs/fetch_transactions.log'))
    ]
)
logger = logging.getLogger('fetch_transactions')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fetch transactions from GoCardless Open Banking API')
    parser.add_argument('--days', type=int, default=7, 
                        help='Number of days to fetch transactions for (default: 7)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit the number of bank connections to process (0 for all)')
    parser.add_argument('--instance-domain', type=str, default=None,
                        help='Process only a specific WHMCS instance by domain')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without actually fetching or storing transactions')
    return parser.parse_args()

def main():
    """Main function to fetch transactions from GoCardless."""
    args = parse_args()
    
    try:
        # Initialize Flask app context
        from app import app
        from models import BankConnection, WhmcsInstance
        from services.gocardless_service import GoCardlessService
        
        with app.app_context():
            logger.info(f"Starting transaction fetch job for past {args.days} days")
            
            # Create GoCardless service
            gocardless_service = GoCardlessService()
            
            # Get all active bank connections
            query = BankConnection.query.filter_by(status='active')
            
            # Apply optional domain filter
            if args.instance_domain:
                whmcs_instance = WhmcsInstance.query.filter_by(domain=args.instance_domain).first()
                if not whmcs_instance:
                    logger.error(f"WHMCS instance with domain {args.instance_domain} not found")
                    return
                query = query.filter_by(whmcs_instance_id=whmcs_instance.id)
            
            bank_connections = query.all()
            
            if args.limit > 0 and len(bank_connections) > args.limit:
                bank_connections = bank_connections[:args.limit]
            
            logger.info(f"Found {len(bank_connections)} active bank connections to process")
            
            if args.dry_run:
                logger.info("DRY RUN: Would process the following connections:")
                for connection in bank_connections:
                    logger.info(f"  - {connection.bank_name} ({connection.account_name}) for {connection.whmcs_instance.domain}")
                return
            
            # Calculate date range for transaction fetch
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
            
            # Process each bank connection
            successful = 0
            failed = 0
            total_transactions = 0
            
            for connection in bank_connections:
                try:
                    logger.info(f"Processing bank connection: {connection.bank_name} - {connection.account_name}")
                    
                    # Get domain from WHMCS instance
                    whmcs_instance = WhmcsInstance.query.get(connection.whmcs_instance_id)
                    if not whmcs_instance:
                        logger.error(f"WHMCS instance not found for bank connection {connection.id}")
                        failed += 1
                        continue
                    
                    # Fetch transactions
                    transactions = gocardless_service.fetch_transactions(
                        domain=whmcs_instance.domain,
                        account_id=connection.account_id,
                        from_date=from_date,
                        to_date=to_date
                    )
                    
                    logger.info(f"Retrieved {len(transactions)} transactions")
                    total_transactions += len(transactions)
                    successful += 1
                    
                except Exception as e:
                    logger.error(f"Error processing bank connection {connection.id}: {str(e)}")
                    failed += 1
            
            logger.info(f"Transaction fetch job completed:")
            logger.info(f"  - Processed: {successful}/{len(bank_connections)} bank connections")
            logger.info(f"  - Failed: {failed}")
            logger.info(f"  - Total transactions: {total_transactions}")
    
    except Exception as e:
        logger.error(f"Unexpected error in transaction fetch job: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
