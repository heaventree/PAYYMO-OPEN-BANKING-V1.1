#!/usr/bin/env python3
"""
Create Test Tenant
This script creates a test tenant for development and testing purposes.
"""

import os
import sys
from datetime import datetime, timedelta
import json
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_backend.app import db, app
from flask_backend.models.auth import User, UserRole, TenantUser
from flask_backend.models.core import Tenant, TenantStatus, PlanType
from werkzeug.security import generate_password_hash

def create_test_tenant():
    """Create a test tenant and admin user"""
    
    with app.app_context():
        print("Checking if test tenant exists...")
        
        # Check if test tenant exists
        tenant = Tenant.query.filter_by(name='Test Company').first()
        if not tenant:
            # Generate a unique slug for the tenant
            slug = f"test-company-{uuid.uuid4().hex[:8]}"
            
            tenant = Tenant(
                name='Test Company',
                slug=slug,
                domain='test.payymo.com',
                status=TenantStatus.ACTIVE.value,
                plan_id=PlanType.PROFESSIONAL.value,
                created_at=datetime.utcnow(),
                trial_ends_at=datetime.utcnow() + timedelta(days=30),
                settings=json.dumps({
                    'theme': 'light',
                    'logo_url': None,
                    'custom_domain': None,
                    'email_notifications': True
                })
            )
            db.session.add(tenant)
            db.session.commit()
            print(f"Created tenant: {tenant.name} with slug: {tenant.slug}")
        
        # Create admin user if it doesn't exist
        user = User.query.filter_by(email='admin@test.com').first()
        if not user:
            user = User(
                tenant_id=tenant.id,  # Set the tenant_id to match our tenant
                name='Admin User',
                email='admin@test.com',
                password_hash=generate_password_hash('password123'),
                role=UserRole.ADMIN.value,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {user.email}")
        
        # Connect user to tenant if not already connected
        tenant_user = TenantUser.query.filter_by(
            tenant_id=tenant.id,
            user_id=user.id
        ).first()
        
        if not tenant_user:
            tenant_user = TenantUser(
                tenant_id=tenant.id,
                user_id=user.id,
                role=UserRole.ADMIN.value,
                is_owner=True,
                created_at=datetime.utcnow()
            )
            db.session.add(tenant_user)
            db.session.commit()
            print(f"Connected user {user.email} to tenant {tenant.name}")
        
        print("Test tenant setup completed!")
        print(f"Login with email: {user.email} and password: password123")
        
        return tenant, user

if __name__ == "__main__":
    create_test_tenant()