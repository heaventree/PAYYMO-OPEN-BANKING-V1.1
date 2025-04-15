"""
Transaction Service Tests

This module contains tests for the transaction service.
"""
import pytest
import hashlib
from datetime import datetime
from flask_backend.services.transaction_service import TransactionService
from flask_backend.utils.error_handler import APIError

def test_transaction_creation(client):
    """Test creating a new transaction"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Transaction data
    transaction_data = {
        'transaction_id': 'test_transaction_001',
        'bank_id': 'test_bank_001',
        'bank_name': 'Test Bank',
        'account_id': 'test_account_001',
        'account_name': 'Test Account',
        'amount': 100.00,
        'currency': 'GBP',
        'description': 'Test Transaction',
        'reference': 'REF001',
        'transaction_date': datetime.utcnow()
    }
    
    # Create the transaction
    transaction = service.create_transaction(transaction_data)
    
    # Assert transaction was created
    assert transaction is not None
    assert transaction.transaction_id == 'test_transaction_001'
    assert transaction.amount == 100.00
    assert transaction.currency == 'GBP'

def test_duplicate_transaction(client):
    """Test creating a duplicate transaction"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Transaction data
    transaction_data = {
        'transaction_id': 'test_transaction_002',
        'amount': 100.00,
        'transaction_date': datetime.utcnow()
    }
    
    # Create the first transaction
    service.create_transaction(transaction_data)
    
    # Try to create a duplicate
    with pytest.raises(APIError) as excinfo:
        service.create_transaction(transaction_data)
    
    # Assert error was raised
    assert "already exists" in str(excinfo.value)

def test_missing_required_fields(client):
    """Test creating a transaction with missing required fields"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Transaction data missing required fields
    transaction_data = {
        'transaction_id': 'test_transaction_003',
        # Missing amount
        'transaction_date': datetime.utcnow()
    }
    
    # Try to create with missing fields
    with pytest.raises(APIError) as excinfo:
        service.create_transaction(transaction_data)
    
    # Assert error was raised
    assert "Missing required field" in str(excinfo.value)

def test_integrity_hash(client):
    """Test transaction integrity hash generation"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Transaction data
    transaction_data = {
        'transaction_id': 'test_transaction_004',
        'bank_id': 'test_bank_001',
        'account_id': 'test_account_001',
        'amount': 100.00,
        'currency': 'GBP',
        'transaction_date': datetime.utcnow()
    }
    
    # Create the transaction
    transaction = service.create_transaction(transaction_data)
    
    # Manually generate hash
    data_string = (
        f"{transaction.transaction_id}|"
        f"{transaction.bank_id or ''}|"
        f"{transaction.account_id or ''}|"
        f"{transaction.amount}|"
        f"{transaction.currency}|"
        f"{transaction.transaction_date.isoformat()}"
    )
    expected_hash = hashlib.sha256(data_string.encode()).hexdigest()
    
    # Generate hash using service method
    actual_hash = service._generate_integrity_hash(transaction)
    
    # Assert hashes match
    assert actual_hash == expected_hash

def test_invoice_match_creation(client, transaction):
    """Test creating an invoice match"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Create an invoice match
    match = service.create_invoice_match(
        transaction_id=transaction.transaction_id,
        invoice_id=12345,
        confidence=0.95,
        match_reason="Reference matches invoice number"
    )
    
    # Assert match was created
    assert match is not None
    assert match.whmcs_invoice_id == 12345
    assert match.confidence == 0.95
    assert match.status == 'pending'

def test_get_transaction(client, transaction):
    """Test retrieving a transaction"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Retrieve the transaction
    retrieved = service.get_transaction(transaction.transaction_id)
    
    # Assert transaction was retrieved
    assert retrieved is not None
    assert retrieved.id == transaction.id
    assert retrieved.transaction_id == transaction.transaction_id

def test_get_nonexistent_transaction(client):
    """Test retrieving a nonexistent transaction"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Try to retrieve a nonexistent transaction
    with pytest.raises(APIError) as excinfo:
        service.get_transaction('nonexistent_transaction')
    
    # Assert error was raised
    assert "not found" in str(excinfo.value)

def test_update_invoice_match(client, transaction):
    """Test updating an existing invoice match"""
    # Create a transaction service instance
    service = TransactionService()
    
    # Create an initial invoice match
    service.create_invoice_match(
        transaction_id=transaction.transaction_id,
        invoice_id=12345,
        confidence=0.7,
        match_reason="Initial match"
    )
    
    # Update the invoice match
    updated_match = service.create_invoice_match(
        transaction_id=transaction.transaction_id,
        invoice_id=12345,
        confidence=0.95,
        match_reason="Updated match reason"
    )
    
    # Assert match was updated
    assert updated_match is not None
    assert updated_match.whmcs_invoice_id == 12345
    assert updated_match.confidence == 0.95
    assert updated_match.match_reason == "Updated match reason"