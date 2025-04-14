import logging
from datetime import datetime, timedelta
from sqlalchemy import text, func
from app import db
from models import (
    ApiLog, LicenseVerification, Transaction, InvoiceMatch,
    BankConnection, LicenseKey
)

logger = logging.getLogger(__name__)

def cleanup_old_logs(days=30):
    """
    Delete logs older than the specified number of days
    
    Args:
        days: Number of days to keep logs for
        
    Returns:
        Number of deleted records
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Delete API logs
        api_logs_deleted = db.session.query(ApiLog).filter(
            ApiLog.created_at < cutoff_date
        ).delete()
        
        # Delete license verification logs
        license_logs_deleted = db.session.query(LicenseVerification).filter(
            LicenseVerification.verified_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        total_deleted = api_logs_deleted + license_logs_deleted
        logger.info(f"Cleaned up {total_deleted} old log records older than {days} days")
        
        return total_deleted
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return 0

def get_database_stats():
    """
    Get statistics about the database tables
    
    Returns:
        Dictionary of database statistics
    """
    try:
        stats = {
            'license_keys': db.session.query(func.count(LicenseKey.id)).scalar() or 0,
            'active_licenses': db.session.query(func.count(LicenseKey.id)).filter(LicenseKey.status == 'active').scalar() or 0,
            'bank_connections': db.session.query(func.count(BankConnection.id)).scalar() or 0,
            'transactions': db.session.query(func.count(Transaction.id)).scalar() or 0,
            'matches': db.session.query(func.count(InvoiceMatch.id)).scalar() or 0,
            'api_logs': db.session.query(func.count(ApiLog.id)).scalar() or 0,
            'license_verifications': db.session.query(func.count(LicenseVerification.id)).scalar() or 0,
            'tables': get_table_sizes()
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {}

def get_table_sizes():
    """
    Get size information for database tables
    
    Returns:
        Dictionary of table names and row counts
    """
    try:
        # Get all table names
        table_names = db.engine.table_names()
        
        # Get row count for each table
        table_sizes = {}
        for table_name in table_names:
            row_count = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            table_sizes[table_name] = row_count
        
        return table_sizes
    
    except Exception as e:
        logger.error(f"Error getting table sizes: {str(e)}")
        return {}

def check_expired_tokens():
    """
    Check for expired OAuth tokens and update their status
    
    Returns:
        Number of connections marked as expired
    """
    try:
        # Find bank connections with expired tokens
        now = datetime.now()
        expired_connections = db.session.query(BankConnection).filter(
            BankConnection.token_expires_at < now,
            BankConnection.status == 'active'
        ).all()
        
        # Update their status to 'expired'
        for connection in expired_connections:
            connection.status = 'expired'
        
        db.session.commit()
        
        count = len(expired_connections)
        if count > 0:
            logger.info(f"Marked {count} bank connections as expired")
        
        return count
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking expired tokens: {str(e)}")
        return 0

def get_recent_activity(limit=10):
    """
    Get recent activity across the system
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        Dictionary of recent activity
    """
    try:
        recent_activity = {
            'verifications': [],
            'transactions': [],
            'matches': []
        }
        
        # Get recent license verifications
        verifications = db.session.query(LicenseVerification).order_by(
            LicenseVerification.verified_at.desc()
        ).limit(limit).all()
        
        for v in verifications:
            recent_activity['verifications'].append({
                'license_key': v.license_key,
                'domain': v.domain,
                'date': v.verified_at.isoformat(),
                'success': v.success,
                'message': v.message
            })
        
        # Get recent transactions
        transactions = db.session.query(Transaction).order_by(
            Transaction.created_at.desc()
        ).limit(limit).all()
        
        for t in transactions:
            recent_activity['transactions'].append({
                'id': t.id,
                'transaction_id': t.transaction_id,
                'bank_name': t.bank_name,
                'account_name': t.account_name,
                'amount': t.amount,
                'currency': t.currency,
                'date': t.transaction_date.isoformat()
            })
        
        # Get recent matches
        matches = db.session.query(InvoiceMatch).order_by(
            InvoiceMatch.created_at.desc()
        ).limit(limit).all()
        
        for m in matches:
            recent_activity['matches'].append({
                'id': m.id,
                'transaction_id': m.transaction_id,
                'invoice_id': m.whmcs_invoice_id,
                'confidence': m.confidence,
                'status': m.status,
                'date': m.created_at.isoformat()
            })
        
        return recent_activity
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return {
            'verifications': [],
            'transactions': [],
            'matches': []
        }
