#!/usr/bin/env python3
"""
GoCardless Open Banking Transaction Matcher

This script processes unmatched transactions and attempts to match them
to WHMCS invoices. It can also auto-apply matches that exceed a certain
confidence threshold. Designed to be run as a cron job.
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
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs/process_matches.log'))
    ]
)
logger = logging.getLogger('process_matches')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process and match transactions to WHMCS invoices')
    parser.add_argument('--days', type=int, default=30,
                        help='Process transactions from the past N days (default: 30)')
    parser.add_argument('--confidence', type=float, default=0.9,
                        help='Auto-apply matches with confidence above this threshold (0.0-1.0, default: 0.9)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit the number of transactions to process (0 for all)')
    parser.add_argument('--instance-domain', type=str, default=None,
                        help='Process only a specific WHMCS instance by domain')
    parser.add_argument('--auto-apply', action='store_true',
                        help='Automatically apply high-confidence matches')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without actually applying matches')
    return parser.parse_args()

def main():
    """Main function to process and match transactions."""
    args = parse_args()
    
    try:
        # Initialize Flask app context
        from app import app, db
        from models import Transaction, InvoiceMatch, WhmcsInstance
        from services.invoice_matching_service import InvoiceMatchingService
        
        with app.app_context():
            logger.info("Starting transaction matching job")
            logger.info(f"Processing transactions from the past {args.days} days")
            
            # Create matching service
            matching_service = InvoiceMatchingService()
            
            # Get unmatched transactions from the specified time period
            cutoff_date = datetime.now() - timedelta(days=args.days)
            
            # Build query for unmatched transactions
            query = Transaction.query.filter(
                Transaction.transaction_date >= cutoff_date,
                ~Transaction.id.in_(
                    db.session.query(InvoiceMatch.transaction_id).filter_by(status='approved')
                )
            )
            
            # Apply optional domain filter
            if args.instance_domain:
                whmcs_instance = WhmcsInstance.query.filter_by(domain=args.instance_domain).first()
                if not whmcs_instance:
                    logger.error(f"WHMCS instance with domain {args.instance_domain} not found")
                    return
                
                # Get bank connections for this instance
                bank_ids = db.session.query(BankConnection.bank_id).filter_by(whmcs_instance_id=whmcs_instance.id).all()
                bank_ids = [b[0] for b in bank_ids]
                
                query = query.filter(Transaction.bank_id.in_(bank_ids))
            
            # Get transactions to process
            unmatched_transactions = query.order_by(Transaction.transaction_date.desc()).all()
            
            if args.limit > 0 and len(unmatched_transactions) > args.limit:
                unmatched_transactions = unmatched_transactions[:args.limit]
            
            logger.info(f"Found {len(unmatched_transactions)} unmatched transactions to process")
            
            if args.dry_run:
                logger.info("DRY RUN: Would process the following transactions:")
                for i, transaction in enumerate(unmatched_transactions[:10]):
                    logger.info(f"  - {transaction.transaction_id}: {transaction.amount} {transaction.currency} ({transaction.transaction_date})")
                if len(unmatched_transactions) > 10:
                    logger.info(f"  ... and {len(unmatched_transactions) - 10} more")
                return
            
            # Process each transaction
            successful = 0
            failed = 0
            total_matches_found = 0
            auto_applied = 0
            
            for transaction in unmatched_transactions:
                try:
                    logger.info(f"Processing transaction: {transaction.transaction_id}")
                    
                    # Find matches for this transaction
                    # In a real implementation, we'd need to determine which WHMCS instance
                    # this transaction belongs to. For now, we'll use a placeholder.
                    whmcs_instance = WhmcsInstance.query.filter(
                        WhmcsInstance.id.in_(
                            db.session.query(BankConnection.whmcs_instance_id).filter_by(bank_id=transaction.bank_id)
                        )
                    ).first()
                    
                    if not whmcs_instance:
                        logger.warning(f"Could not determine WHMCS instance for transaction {transaction.transaction_id}")
                        failed += 1
                        continue
                    
                    # Find matches
                    try:
                        match_result = matching_service.find_matches(
                            domain=whmcs_instance.domain,
                            transaction_id=transaction.transaction_id
                        )
                        
                        matches_found = match_result.get('matches_found', 0)
                        matches = match_result.get('matches', [])
                        
                        logger.info(f"Found {matches_found} potential matches")
                        total_matches_found += matches_found
                        
                        # Auto-apply high-confidence matches if enabled
                        if args.auto_apply and matches_found > 0:
                            # Find the highest confidence match
                            best_match = max(matches, key=lambda x: x['confidence']) if matches else None
                            
                            if best_match and best_match['confidence'] >= args.confidence:
                                logger.info(f"Auto-applying match with confidence {best_match['confidence']} to invoice {best_match['invoice_id']}")
                                
                                # Apply the match
                                apply_result = matching_service.apply_match(
                                    domain=whmcs_instance.domain,
                                    match_id=best_match['id']
                                )
                                
                                if apply_result.get('success'):
                                    logger.info(f"Successfully applied match: {apply_result.get('message')}")
                                    auto_applied += 1
                                else:
                                    logger.warning(f"Failed to apply match: {apply_result.get('message')}")
                        
                        successful += 1
                        
                    except Exception as e:
                        logger.error(f"Error finding matches for transaction {transaction.transaction_id}: {str(e)}")
                        failed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
                    failed += 1
            
            logger.info(f"Transaction matching job completed:")
            logger.info(f"  - Processed: {successful}/{len(unmatched_transactions)} transactions")
            logger.info(f"  - Failed: {failed}")
            logger.info(f"  - Total matches found: {total_matches_found}")
            if args.auto_apply:
                logger.info(f"  - Auto-applied: {auto_applied}")
    
    except Exception as e:
        logger.error(f"Unexpected error in transaction matching job: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
