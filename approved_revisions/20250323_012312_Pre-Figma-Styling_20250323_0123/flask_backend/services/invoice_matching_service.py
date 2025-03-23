import json
import logging
from datetime import datetime
from flask_backend.app import db
from flask_backend.models import Transaction, InvoiceMatch, WhmcsInstance, BankConnection
from flask_backend.utils.error_handler import APIError

logger = logging.getLogger(__name__)

class InvoiceMatchingService:
    """Service for matching bank transactions to WHMCS invoices"""
    
    def __init__(self):
        self.min_confidence = 0.5  # Minimum confidence threshold for match suggestions
    
    def find_matches(self, domain, transaction_id):
        """
        Find possible invoice matches for a transaction
        
        Args:
            domain: WHMCS instance domain
            transaction_id: Transaction ID to find matches for
            
        Returns:
            Dictionary of matching results
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", 404)
        
        # Find the transaction
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        
        if not transaction:
            raise APIError(f"Transaction not found: {transaction_id}", 404)
        
        # Check if transaction is already matched
        existing_matches = InvoiceMatch.query.filter_by(
            transaction_id=transaction.id,
            status='approved'
        ).first()
        
        if existing_matches:
            return {
                'already_matched': True,
                'matches_found': 0,
                'matches': []
            }
        
        # Find unpaid invoices using the WHMCS instance
        unpaid_invoices = self._get_unpaid_invoices(whmcs_instance)
        
        if not unpaid_invoices:
            return {
                'already_matched': False,
                'matches_found': 0,
                'matches': []
            }
        
        # Apply matching algorithms to find potential matches
        matches = []
        match_count = 0
        
        for invoice in unpaid_invoices:
            # Calculate match confidence and reason
            match_result = self._calculate_match_confidence(transaction, invoice)
            
            if match_result['confidence'] >= self.min_confidence:
                # Check if match already exists
                existing_match = InvoiceMatch.query.filter_by(
                    transaction_id=transaction.id,
                    whmcs_invoice_id=invoice['id']
                ).first()
                
                if existing_match:
                    # Update existing match if needed
                    if existing_match.confidence < match_result['confidence']:
                        existing_match.confidence = match_result['confidence']
                        existing_match.match_reason = match_result['reason']
                        existing_match.updated_at = datetime.now()
                        db.session.commit()
                    
                    match_info = {
                        'id': existing_match.id,
                        'invoice_id': invoice['id'],
                        'confidence': existing_match.confidence,
                        'reason': existing_match.match_reason,
                        'status': existing_match.status,
                        'invoice': invoice
                    }
                    matches.append(match_info)
                else:
                    # Create new match record
                    new_match = InvoiceMatch(
                        transaction_id=transaction.id,
                        whmcs_invoice_id=invoice['id'],
                        confidence=match_result['confidence'],
                        match_reason=match_result['reason'],
                        status='pending'
                    )
                    
                    db.session.add(new_match)
                    db.session.commit()
                    
                    match_info = {
                        'id': new_match.id,
                        'invoice_id': invoice['id'],
                        'confidence': new_match.confidence,
                        'reason': new_match.match_reason,
                        'status': new_match.status,
                        'invoice': invoice
                    }
                    matches.append(match_info)
                
                match_count += 1
        
        # Sort matches by confidence (descending)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'already_matched': False,
            'matches_found': match_count,
            'matches': matches
        }
    
    def apply_match(self, domain, match_id):
        """
        Apply a match between a transaction and an invoice
        
        Args:
            domain: WHMCS instance domain
            match_id: Match ID to apply
            
        Returns:
            Dictionary with result information
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", 404)
        
        # Find the match
        match = InvoiceMatch.query.filter_by(id=match_id).first()
        
        if not match:
            raise APIError(f"Match not found: {match_id}", 404)
        
        if match.status == 'approved':
            return {
                'success': True,
                'message': 'Match was already approved',
                'match_id': match_id
            }
        
        # Find the transaction
        transaction = Transaction.query.filter_by(id=match.transaction_id).first()
        
        if not transaction:
            raise APIError("Transaction not found for this match", 404)
        
        # Apply the payment to the invoice in WHMCS
        apply_result = self._apply_payment_to_invoice(
            whmcs_instance,
            match.whmcs_invoice_id,
            transaction
        )
        
        if apply_result['success']:
            # Update the match status
            match.status = 'approved'
            match.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Match approved and payment applied - Match ID: {match_id}, Transaction: {transaction.transaction_id}, Invoice: {match.whmcs_invoice_id}")
            
            return {
                'success': True,
                'message': 'Payment successfully applied to invoice',
                'match_id': match_id,
                'invoice_id': match.whmcs_invoice_id,
                'transaction_id': transaction.transaction_id
            }
        else:
            return {
                'success': False,
                'message': apply_result['message'],
                'match_id': match_id
            }
    
    def reject_match(self, domain, match_id):
        """
        Reject a match between a transaction and an invoice
        
        Args:
            domain: WHMCS instance domain
            match_id: Match ID to reject
            
        Returns:
            Dictionary with result information
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", 404)
        
        # Find the match
        match = InvoiceMatch.query.filter_by(id=match_id).first()
        
        if not match:
            raise APIError(f"Match not found: {match_id}", 404)
        
        if match.status == 'rejected':
            return {
                'success': True,
                'message': 'Match was already rejected',
                'match_id': match_id
            }
        
        # Update the match status
        match.status = 'rejected'
        match.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Match rejected - Match ID: {match_id}, Invoice: {match.whmcs_invoice_id}")
        
        return {
            'success': True,
            'message': 'Match rejected successfully',
            'match_id': match_id
        }
    
    def process_new_invoice(self, domain, invoice_id):
        """
        Process a new invoice to find matching transactions
        
        Args:
            domain: WHMCS instance domain
            invoice_id: Invoice ID to process
            
        Returns:
            Dictionary with matching results
        """
        # Find the WHMCS instance
        whmcs_instance = WhmcsInstance.query.filter_by(domain=domain).first()
        
        if not whmcs_instance:
            raise APIError(f"WHMCS instance not found for domain: {domain}", 404)
        
        # Get invoice details
        invoice = self._get_invoice_details(whmcs_instance, invoice_id)
        
        if not invoice:
            raise APIError(f"Invoice not found: {invoice_id}", 404)
        
        # Get unmatched transactions from the last 30 days
        thirty_days_ago = datetime.now().date().replace(day=datetime.now().day - 30)
        unmatched_transactions = Transaction.query.filter(
            Transaction.transaction_date >= thirty_days_ago,
            ~Transaction.id.in_(
                db.session.query(InvoiceMatch.transaction_id).filter_by(status='approved')
            )
        ).all()
        
        # Apply matching algorithms to find potential matches
        matches = []
        match_count = 0
        
        for transaction in unmatched_transactions:
            # Calculate match confidence and reason
            match_result = self._calculate_match_confidence(transaction, invoice)
            
            if match_result['confidence'] >= self.min_confidence:
                # Check if match already exists
                existing_match = InvoiceMatch.query.filter_by(
                    transaction_id=transaction.id,
                    whmcs_invoice_id=invoice['id']
                ).first()
                
                if existing_match:
                    # Update existing match if needed
                    if existing_match.confidence < match_result['confidence']:
                        existing_match.confidence = match_result['confidence']
                        existing_match.match_reason = match_result['reason']
                        existing_match.updated_at = datetime.now()
                        db.session.commit()
                    
                    match_info = {
                        'id': existing_match.id,
                        'transaction_id': transaction.id,
                        'confidence': existing_match.confidence,
                        'reason': existing_match.match_reason,
                        'status': existing_match.status
                    }
                    matches.append(match_info)
                else:
                    # Create new match record
                    new_match = InvoiceMatch(
                        transaction_id=transaction.id,
                        whmcs_invoice_id=invoice['id'],
                        confidence=match_result['confidence'],
                        match_reason=match_result['reason'],
                        status='pending'
                    )
                    
                    db.session.add(new_match)
                    db.session.commit()
                    
                    match_info = {
                        'id': new_match.id,
                        'transaction_id': transaction.id,
                        'confidence': new_match.confidence,
                        'reason': new_match.match_reason,
                        'status': new_match.status
                    }
                    matches.append(match_info)
                
                match_count += 1
        
        return {
            'invoice_id': invoice_id,
            'matches_found': match_count,
            'matches': matches
        }
    
    def _calculate_match_confidence(self, transaction, invoice):
        """
        Calculate match confidence between a transaction and an invoice
        
        Args:
            transaction: Transaction object
            invoice: Invoice dictionary
            
        Returns:
            Dictionary with confidence score and reason
        """
        # Initialize confidence and reasons
        confidence = 0.0
        reasons = []
        
        # 1. Amount matching
        amount_result = self._check_amount_match(transaction.amount, invoice)
        confidence += amount_result['confidence_factor']
        if amount_result['reason']:
            reasons.append(amount_result['reason'])
        
        # 2. Reference matching
        if transaction.reference:
            reference_result = self._check_reference_match(transaction.reference, invoice)
            confidence += reference_result['confidence_factor']
            if reference_result['reason']:
                reasons.append(reference_result['reason'])
        
        # 3. Description matching (client name in description)
        if transaction.description and invoice.get('client_name'):
            description_result = self._check_description_match(
                transaction.description, 
                invoice.get('client_name', '')
            )
            confidence += description_result['confidence_factor']
            if description_result['reason']:
                reasons.append(description_result['reason'])
        
        # 4. Date proximity
        date_result = self._check_date_proximity(
            transaction.transaction_date, 
            datetime.strptime(invoice['date'], '%Y-%m-%d')
        )
        confidence += date_result['confidence_factor']
        if date_result['reason']:
            reasons.append(date_result['reason'])
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return {
            'confidence': confidence,
            'reason': '; '.join(reasons)
        }
    
    def _check_amount_match(self, transaction_amount, invoice):
        """Check if transaction amount matches invoice amount"""
        invoice_amount = float(invoice.get('total', 0))
        invoice_balance = float(invoice.get('balance', 0))
        
        # Exact match with balance
        if abs(transaction_amount - invoice_balance) < 0.01:
            return {
                'confidence_factor': 0.7,
                'reason': 'Exact amount match'
            }
        
        # Partial payment
        if transaction_amount < invoice_balance:
            percentage = (transaction_amount / invoice_balance) * 100
            
            if abs(percentage - 50) < 1:
                return {
                    'confidence_factor': 0.5,
                    'reason': 'Partial payment (50%)'
                }
            elif abs(percentage - 25) < 1:
                return {
                    'confidence_factor': 0.4,
                    'reason': 'Partial payment (25%)'
                }
            elif abs(percentage - 75) < 1:
                return {
                    'confidence_factor': 0.5,
                    'reason': 'Partial payment (75%)'
                }
            else:
                return {
                    'confidence_factor': 0.3,
                    'reason': f'Partial payment ({round(percentage)}%)'
                }
        
        # Transaction slightly higher (possible fees)
        if transaction_amount > invoice_balance and transaction_amount <= (invoice_balance * 1.05):
            return {
                'confidence_factor': 0.6,
                'reason': 'Amount slightly higher (possible fees)'
            }
        
        # No match
        return {
            'confidence_factor': 0.0,
            'reason': ''
        }
    
    def _check_reference_match(self, reference, invoice):
        """Check if transaction reference matches invoice details"""
        # Clean up reference
        reference = ''.join(filter(str.isalnum, reference)).lower()
        
        # Direct match with invoice ID
        if str(invoice['id']) in reference:
            return {
                'confidence_factor': 0.8,
                'reason': 'Invoice ID in reference'
            }
        
        # Check for invoice number in reference
        if invoice.get('invoicenum') and str(invoice['invoicenum']) in reference:
            return {
                'confidence_factor': 0.8,
                'reason': 'Invoice number in reference'
            }
        
        # No match
        return {
            'confidence_factor': 0.0,
            'reason': ''
        }
    
    def _check_description_match(self, description, client_name):
        """Check if client name appears in transaction description"""
        description_lower = description.lower()
        client_name_lower = client_name.lower()
        
        # Split client name into parts
        name_parts = client_name_lower.split()
        word_matches = 0
        
        # Count how many parts of the name appear in the description
        for part in name_parts:
            if len(part) > 2 and part in description_lower:
                word_matches += 1
        
        if word_matches > 0:
            # Calculate confidence based on number of matches
            confidence = min(0.3 + (word_matches * 0.1), 0.6)
            return {
                'confidence_factor': confidence,
                'reason': 'Client name in description'
            }
        
        # No match
        return {
            'confidence_factor': 0.0,
            'reason': ''
        }
    
    def _check_date_proximity(self, transaction_date, invoice_date):
        """Check the time proximity between transaction and invoice dates"""
        days_difference = abs((transaction_date - invoice_date).days)
        
        if days_difference <= 1:
            return {
                'confidence_factor': 0.2,
                'reason': 'Same day or next day'
            }
        elif days_difference <= 3:
            return {
                'confidence_factor': 0.15,
                'reason': 'Within 3 days'
            }
        elif days_difference <= 7:
            return {
                'confidence_factor': 0.1,
                'reason': 'Within 1 week'
            }
        elif days_difference <= 14:
            return {
                'confidence_factor': 0.05,
                'reason': 'Within 2 weeks'
            }
        
        # Too far apart
        return {
            'confidence_factor': 0.0,
            'reason': ''
        }
    
    def _get_unpaid_invoices(self, whmcs_instance):
        """Get unpaid invoices from WHMCS instance"""
        # In a real implementation, this would call the WHMCS API
        # For this project, we'll return a mock response
        
        # Example of a real implementation:
        # api_identifier = whmcs_instance.api_identifier
        # api_secret = whmcs_instance.api_secret
        # domain = whmcs_instance.domain
        
        # api_response = requests.post(
        #     f"https://{domain}/includes/api.php",
        #     data={
        #         'identifier': api_identifier,
        #         'secret': api_secret,
        #         'action': 'GetInvoices',
        #         'status': 'Unpaid',
        #         'limitnum': 100,
        #         'responsetype': 'json'
        #     }
        # )
        
        # if api_response.status_code == 200:
        #     data = api_response.json()
        #     if data.get('result') == 'success':
        #         return data.get('invoices', {}).get('invoice', [])
        
        # For now, return an empty list - this would be replaced with actual API call
        return []
    
    def _get_invoice_details(self, whmcs_instance, invoice_id):
        """Get invoice details from WHMCS instance"""
        # In a real implementation, this would call the WHMCS API
        # For this project, we'll return a mock response
        
        # Example of a real implementation:
        # api_identifier = whmcs_instance.api_identifier
        # api_secret = whmcs_instance.api_secret
        # domain = whmcs_instance.domain
        
        # api_response = requests.post(
        #     f"https://{domain}/includes/api.php",
        #     data={
        #         'identifier': api_identifier,
        #         'secret': api_secret,
        #         'action': 'GetInvoice',
        #         'invoiceid': invoice_id,
        #         'responsetype': 'json'
        #     }
        # )
        
        # if api_response.status_code == 200:
        #     data = api_response.json()
        #     if data.get('result') == 'success':
        #         return data
        
        # For now, return None - this would be replaced with actual API call
        return None
    
    def _apply_payment_to_invoice(self, whmcs_instance, invoice_id, transaction):
        """Apply a payment to an invoice in WHMCS"""
        # In a real implementation, this would call the WHMCS API
        # For this project, we'll return a mock response
        
        # Example of a real implementation:
        # api_identifier = whmcs_instance.api_identifier
        # api_secret = whmcs_instance.api_secret
        # domain = whmcs_instance.domain
        
        # api_response = requests.post(
        #     f"https://{domain}/includes/api.php",
        #     data={
        #         'identifier': api_identifier,
        #         'secret': api_secret,
        #         'action': 'AddInvoicePayment',
        #         'invoiceid': invoice_id,
        #         'transid': transaction.transaction_id,
        #         'gateway': 'GoCardless Open Banking',
        #         'amount': transaction.amount,
        #         'date': transaction.transaction_date.strftime('%Y-%m-%d'),
        #         'responsetype': 'json'
        #     }
        # )
        
        # if api_response.status_code == 200:
        #     data = api_response.json()
        #     if data.get('result') == 'success':
        #         return {'success': True, 'message': 'Payment applied successfully'}
        #     else:
        #         return {'success': False, 'message': data.get('message', 'Unknown error')}
        
        # For now, simulate a successful response - this would be replaced with actual API call
        return {'success': True, 'message': 'Payment applied successfully'}
