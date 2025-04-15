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
        "email": f"{username}@example.com",
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

def main():
    """Main function to run all tests"""
    logger.info("Starting JWT authentication tests")
    
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
    
    # Test login
    login_data = test_login(email, password)
    
    logger.info("JWT authentication tests completed")

if __name__ == "__main__":
    main()