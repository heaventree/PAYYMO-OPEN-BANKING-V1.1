"""
Authentication Tests

This module contains tests for authentication-related functionality.
"""
import json
import pytest
from flask import session, url_for
from flask_backend.models import LicenseKey, WhmcsInstance
from werkzeug.security import generate_password_hash, check_password_hash

def test_license_key_validation(client, license_key):
    """Test license key validation"""
    # Create a license verification API endpoint mock
    response = client.post('/api/license/verify', json={
        'license_key': license_key.key,
        'domain': 'test.example.com'
    })
    
    # Assert response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is True
    assert data['status'] == 'active'

def test_invalid_license_key(client):
    """Test invalid license key"""
    # Try to verify an invalid license key
    response = client.post('/api/license/verify', json={
        'license_key': 'INVALID-LICENSE-KEY',
        'domain': 'test.example.com'
    })
    
    # Assert response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['valid'] is False
    assert 'error' in data

def test_license_domain_restriction(client, license_key):
    """Test license key domain restriction"""
    # Try to verify a license key on an unauthorized domain
    response = client.post('/api/license/verify', json={
        'license_key': license_key.key,
        'domain': 'unauthorized.example.com'
    })
    
    # Assert response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['valid'] is False
    assert 'domain' in data['error'].lower()

def test_webhook_authentication(client, whmcs_instance):
    """Test webhook authentication"""
    # Mock webhook with correct secret
    response = client.post('/api/webhook/gocardless', 
        json={'test': 'data'},
        headers={'X-Webhook-Secret': whmcs_instance.webhook_secret}
    )
    
    # Response could be 404 as the webhook isn't truly processed, but auth should pass
    assert response.status_code != 401

    # Try with incorrect secret
    response = client.post('/api/webhook/gocardless', 
        json={'test': 'data'},
        headers={'X-Webhook-Secret': 'wrong-secret'}
    )
    
    # Should be unauthorized
    assert response.status_code == 401

def test_api_key_rotation(client, whmcs_instance):
    """Test API key rotation"""
    # Setup initial state
    original_api_secret = whmcs_instance.api_secret
    
    # Request API key rotation
    response = client.post('/api/instance/rotate-keys', json={
        'domain': whmcs_instance.domain,
        'api_identifier': whmcs_instance.api_identifier,
        'api_secret': original_api_secret
    })
    
    # Assert response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'new_api_secret' in data
    assert data['new_api_secret'] != original_api_secret

def test_password_hashing():
    """Test password hashing implementation"""
    password = "SecurePassword123!"
    
    # Test hash generation
    password_hash = generate_password_hash(password)
    assert password_hash != password
    
    # Test hash verification
    assert check_password_hash(password_hash, password) is True
    assert check_password_hash(password_hash, "WrongPassword") is False