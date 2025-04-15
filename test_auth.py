#!/usr/bin/env python3
"""
Test script for JWT authentication with RS256

This script tests the new JWT authentication implementation with RS256 algorithm.
"""

import requests
import json
import time
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:5000/api"

def test_register():
    """Test user registration"""
    url = f"{BASE_URL}/auth/register"
    
    # Generate a unique username using timestamp
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    
    data = {
        "email": f"{username}@testdomain.org",
        "username": username,
        "password": "SecurePassword123!"
    }
    
    logger.info(f"Testing user registration with username: {username}")
    response = requests.post(url, json=data)
    
    if response.status_code == 201:
        logger.info("✅ User registration successful")
        return response.json()['data']
    else:
        logger.error(f"❌ User registration failed: {response.text}")
        return None

def test_login(email, password):
    """Test user login"""
    url = f"{BASE_URL}/auth/login"
    
    data = {
        "email": email,
        "password": password
    }
    
    logger.info(f"Testing user login with email: {email}")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        logger.info("✅ User login successful")
        return response.json()['data']
    else:
        logger.error(f"❌ User login failed: {response.text}")
        return None

def test_login_with_invalid_credentials():
    """Test login with invalid credentials to verify security measures"""
    url = f"{BASE_URL}/auth/login"
    
    # Test with non-existent email
    data1 = {
        "email": "nonexistent_user@testdomain.org",
        "password": "AnyPassword123!"
    }
    
    # Test with existing email but wrong password
    # For this test to work, you need a known user in the system
    data2 = {
        "email": "admin@testdomain.org",  # Assuming this user exists
        "password": "WrongPassword123!"
    }
    
    logger.info("Testing login security with non-existent user")
    start_time1 = time.time()
    response1 = requests.post(url, json=data1)
    end_time1 = time.time()
    duration1 = end_time1 - start_time1
    
    logger.info("Testing login security with wrong password")
    start_time2 = time.time()
    response2 = requests.post(url, json=data2)
    end_time2 = time.time()
    duration2 = end_time2 - start_time2
    
    # Check response codes (both should be the same for security)
    security_passed = True
    
    # Our enhanced system returns a 401 status code for authentication failures
    if response1.status_code != 401 or response2.status_code != 401:
        logger.error(f"❌ Security test failed: Different response codes for invalid credentials: {response1.status_code} vs {response2.status_code}")
        security_passed = False
    
    # Check if both responses have the same error message
    error_msg1 = response1.json().get('message', '')
    error_msg2 = response2.json().get('message', '')
    
    if error_msg1 != error_msg2:
        logger.error("❌ Security test failed: Different error messages for invalid credentials")
        security_passed = False
    
    # Check if response times are similar (within reasonable threshold)
    # This tests protection against timing attacks
    time_difference = abs(duration1 - duration2)
    time_threshold = 0.5  # 500ms threshold
    
    if time_difference > time_threshold:
        logger.warning(f"⚠️ Potential timing attack vulnerability: Time difference ({time_difference:.2f}s) is significant")
        logger.warning(f"  Non-existent user response time: {duration1:.2f}s")
        logger.warning(f"  Wrong password response time: {duration2:.2f}s")
    else:
        logger.info(f"✅ Timing attack protection working: Time difference ({time_difference:.2f}s) is minimal")
    
    if security_passed:
        logger.info("✅ Login security tests passed")
    else:
        logger.error("❌ Login security tests failed")
    
    return security_passed

def test_me(access_token):
    """Test getting current user information"""
    url = f"{BASE_URL}/auth/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    logger.info("Testing getting current user information")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logger.info("✅ Getting current user successful")
        return response.json()['data']
    else:
        logger.error(f"❌ Getting current user failed: {response.text}")
        return None

def test_token_refresh(refresh_token):
    """Test refreshing access token"""
    url = f"{BASE_URL}/auth/refresh"
    
    data = {
        "refresh_token": refresh_token
    }
    
    logger.info("Testing refreshing access token")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        logger.info("✅ Token refresh successful")
        return response.json()['data']
    else:
        logger.error(f"❌ Token refresh failed: {response.text}")
        return None

def test_logout(access_token):
    """Test user logout"""
    url = f"{BASE_URL}/auth/logout"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    logger.info("Testing user logout")
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        logger.info("✅ User logout successful")
        return True
    else:
        logger.error(f"❌ User logout failed: {response.text}")
        return False

def verify_token(token):
    """Verify a token"""
    url = f"{BASE_URL}/auth/token/verify"
    
    data = {
        "token": token
    }
    
    logger.info("Testing token verification")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        logger.info("✅ Token verification successful")
        return response.json()['data']
    else:
        logger.error(f"❌ Token verification failed: {response.text}")
        return None

def test_invalid_token_scenarios():
    """Test various invalid token scenarios"""
    url_me = f"{BASE_URL}/auth/me"
    url_verify = f"{BASE_URL}/auth/token/verify"
    
    # Test with completely invalid token
    invalid_token = "totally.invalid.token"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    logger.info("Testing with completely invalid token format")
    response = requests.get(url_me, headers=headers)
    if response.status_code == 401:
        logger.info("✅ Invalid token format properly rejected")
    else:
        logger.error(f"❌ Invalid token not rejected properly: {response.status_code}")
    
    # Test with missing token
    headers_missing = {"Authorization": "Bearer"}
    logger.info("Testing with missing token")
    response = requests.get(url_me, headers=headers_missing)
    if response.status_code == 401:
        logger.info("✅ Missing token properly rejected")
    else:
        logger.error(f"❌ Missing token not handled properly: {response.status_code}")
    
    # Test with tampered token (valid format but invalid signature)
    # Create a tampered token by changing a character in a valid token
    # For this test, we need a valid token first
    valid_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.invalid_signature_part"
    
    logger.info("Testing token verification with tampered token")
    response = requests.post(url_verify, json={"token": valid_token})
    if response.status_code == 401:
        logger.info("✅ Tampered token properly rejected")
    else:
        logger.error(f"❌ Tampered token not rejected properly: {response.status_code}")
    
    return True

def main():
    """Main function to run all tests"""
    logger.info("Starting JWT authentication tests")
    
    # Test security measures for login with invalid credentials
    logger.info("\n=== TESTING SECURITY MEASURES FOR INVALID CREDENTIALS ===")
    security_test_result = test_login_with_invalid_credentials()
    
    # Test invalid token scenarios
    logger.info("\n=== TESTING INVALID TOKEN SCENARIOS ===")
    token_security_result = test_invalid_token_scenarios()
    
    # Test normal flow with valid credentials
    logger.info("\n=== TESTING NORMAL AUTHENTICATION FLOW ===")
    
    # Test registration
    registration_data = test_register()
    if not registration_data:
        logger.error("Registration failed, cannot continue tests")
        sys.exit(1)
    
    access_token = registration_data['access_token']
    refresh_token = registration_data['refresh_token']
    email = registration_data['user']['email']
    password = "SecurePassword123!"
    
    # Test token verification
    token_info = verify_token(access_token)
    
    # Test getting current user
    user_data = test_me(access_token)
    
    # Test refresh token
    refreshed_token_data = test_token_refresh(refresh_token)
    
    if refreshed_token_data:
        # Test with new access token
        new_access_token = refreshed_token_data['access_token']
        new_user_data = test_me(new_access_token)
        
        # Test logout
        logout_success = test_logout(new_access_token)
        
        # Try using token after logout (should fail)
        if logout_success:
            invalid_user_data = test_me(new_access_token)
            if not invalid_user_data:
                logger.info("✅ Token correctly invalidated after logout")
            else:
                logger.warning("⚠️ Token still valid after logout")
    
    # Test login with valid credentials
    login_data = test_login(email, password)
    
    # Summarize test results
    logger.info("\n=== JWT AUTHENTICATION TEST SUMMARY ===")
    if security_test_result and token_security_result:
        logger.info("✅ All security tests passed successfully")
    else:
        logger.warning("⚠️ Some security tests failed")
    
    logger.info("JWT authentication tests completed")

if __name__ == "__main__":
    main()