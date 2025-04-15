"""
Transaction Service

This module provides secure transaction handling with audit trails and integrity checks.
"""
import json
import logging
import hashlib
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask import current_app
from flask_backend.services.base_service import BaseService
from flask_backend.models import Transaction, InvoiceMatch, ApiLog
from flask_backend.utils.error_handler import APIError

logger = logging.getLogger(__name__)

def get_db():
    """Get SQLAlchemy db instance from current app"""
    if current_app:
        return current_app.extensions['sqlalchemy'].db
    return None

class TransactionService(BaseService):
    """Service for secure transaction handling"""
    
    def __init__(self):
        """Initialize the transaction service"""
        self._app = None
        self._initialized = False
        
    def init_app(self, app):
        """
        Initialize the service with the Flask app
        
        Args:
            app: Flask application instance
        """
        self._app = app
        self._initialized = True
        logger.info("Transaction service initialized successfully")
        
    @property
    def initialized(self):
        """
        Return whether the service is initialized
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized
        
    def health_check(self):
        """
        Return the health status of the service
        
        Returns:
            dict: Health status information with at least 'status' and 'message' keys
        """
        status = "ok" if self._initialized else "error"
        message = f"Transaction service is {'initialized' if self._initialized else 'not initialized'}"
            
        return {
            "status": status,
            "message": message
        }
    
    def create_transaction(self, transaction_data):
        """
        Create a new transaction with integrity check
        
        Args:
            transaction_data: Dictionary containing transaction data
            
        Returns:
            Created transaction object
        """
        if not transaction_data:
            raise APIError("No transaction data provided", status_code=400)
        
        # Required fields
        required_fields = ['transaction_id', 'amount', 'transaction_date']
        for field in required_fields:
            if field not in transaction_data:
                raise APIError(f"Missing required field: {field}", status_code=400)
        
        # Get database connection
        db = get_db()
        if not db:
            raise APIError("Database connection error", status_code=500)
            
        # Check if transaction already exists
        existing = Transaction.query.filter_by(transaction_id=transaction_data['transaction_id']).first()
        if existing:
            raise APIError("Transaction already exists", status_code=409)
        
        try:
            # Create transaction object with allowed fields only (prevents mass assignment)
            transaction = Transaction(
                transaction_id=transaction_data['transaction_id'],
                bank_id=transaction_data.get('bank_id'),
                bank_name=transaction_data.get('bank_name'),
                account_id=transaction_data.get('account_id'),
                account_name=transaction_data.get('account_name'),
                amount=float(transaction_data['amount']),
                currency=transaction_data.get('currency', 'GBP'),
                description=transaction_data.get('description'),
                reference=transaction_data.get('reference'),
                transaction_date=transaction_data['transaction_date'] if isinstance(transaction_data['transaction_date'], datetime) else 
                                datetime.fromisoformat(transaction_data['transaction_date'].replace('Z', '+00:00')),
                created_at=datetime.utcnow()
            )
            
            # Generate integrity hash for auditing
            transaction_integrity_hash = self._generate_integrity_hash(transaction)
            
            # Get database connection
            db = get_db()
            if not db:
                raise APIError("Database connection error", status_code=500)
                
            # Add to database
            db.session.add(transaction)
            
            # Create audit log
            log = ApiLog(
                endpoint='transaction/create',
                method='CREATE',
                request_data=json.dumps(transaction_data),
                response_data=json.dumps({'transaction_id': transaction.transaction_id, 'integrity_hash': transaction_integrity_hash}),
                status_code=201,
                ip_address='internal',
                user_agent='transaction_service',
                duration_ms=0,
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            
            # Commit transaction
            db.session.commit()
            
            logger.info(f"Created transaction: {transaction.transaction_id}")
            return transaction
            
        except IntegrityError as e:
            # Get database connection
            db = get_db()
            if db:
                db.session.rollback()
            logger.error(f"IntegrityError creating transaction: {str(e)}")
            raise APIError("Could not create transaction: integrity error", status_code=500)
            
        except Exception as e:
            # Get database connection
            db = get_db()
            if db:
                db.session.rollback()
            logger.error(f"Error creating transaction: {str(e)}")
            raise APIError(f"Could not create transaction: {str(e)}", status_code=500)
    
    def get_transaction(self, transaction_id):
        """
        Get a transaction by ID with integrity check
        
        Args:
            transaction_id: ID of the transaction to retrieve
            
        Returns:
            Transaction object
        """
        # Get database connection
        db = get_db()
        if not db:
            raise APIError("Database connection error", status_code=500)
            
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        
        if not transaction:
            raise APIError("Transaction not found", status_code=404)
        
        # Verify integrity hash
        current_hash = self._generate_integrity_hash(transaction)
        
        # In a production system, this hash would be stored separately for verification
        # For now, we're just logging the computed hash
        logger.info(f"Transaction integrity hash: {current_hash}")
        
        return transaction
    
    def create_invoice_match(self, transaction_id, invoice_id, confidence, match_reason):
        """
        Create a match between a transaction and an invoice
        
        Args:
            transaction_id: ID of the transaction
            invoice_id: ID of the WHMCS invoice
            confidence: Confidence level of the match (0.0-1.0)
            match_reason: Reason for the match
            
        Returns:
            Created match object
        """
        if not transaction_id or not invoice_id:
            raise APIError("Missing transaction_id or invoice_id", status_code=400)
        
        # Find the transaction
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if not transaction:
            raise APIError("Transaction not found", status_code=404)
        
        try:
            # Check if match already exists
            existing = InvoiceMatch.query.filter_by(
                transaction_id=transaction.id,
                whmcs_invoice_id=invoice_id
            ).first()
            
            if existing:
                # Update existing match
                existing.confidence = confidence
                existing.match_reason = match_reason
                existing.updated_at = datetime.utcnow()
                match = existing
            else:
                # Create new match
                match = InvoiceMatch(
                    transaction_id=transaction.id,
                    whmcs_invoice_id=invoice_id,
                    confidence=confidence,
                    match_reason=match_reason,
                    status='pending',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(match)
            
            # Create audit log
            log = ApiLog(
                endpoint='invoice_match/create',
                method='CREATE' if not existing else 'UPDATE',
                request_data=json.dumps({
                    'transaction_id': transaction_id,
                    'invoice_id': invoice_id,
                    'confidence': confidence,
                    'match_reason': match_reason
                }),
                response_data=json.dumps({'id': match.id if not existing else existing.id}),
                status_code=201 if not existing else 200,
                ip_address='internal',
                user_agent='transaction_service',
                duration_ms=0,
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            
            # Commit transaction
            db.session.commit()
            
            logger.info(f"Created/updated invoice match: Transaction {transaction_id} -> Invoice {invoice_id}")
            return match
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating invoice match: {str(e)}")
            raise APIError(f"Could not create invoice match: {str(e)}", status_code=500)
    
    def _generate_integrity_hash(self, transaction):
        """
        Generate an integrity hash for a transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            SHA-256 hash of transaction data
        """
        # Create a string representation of key transaction data
        data_string = (
            f"{transaction.transaction_id}|"
            f"{transaction.bank_id or ''}|"
            f"{transaction.account_id or ''}|"
            f"{transaction.amount}|"
            f"{transaction.currency}|"
            f"{transaction.transaction_date.isoformat()}"
        )
        
        # Generate SHA-256 hash
        return hashlib.sha256(data_string.encode()).hexdigest()

# Create singleton instance
transaction_service = TransactionService()