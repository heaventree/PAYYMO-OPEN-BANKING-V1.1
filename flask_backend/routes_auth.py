"""
Authentication Routes
-----------------
Routes for user authentication and token management.
"""

import logging
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_backend.services.auth_service import auth_service
from flask_backend.models import User, db

# Logger
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Log in a user and return access and refresh tokens"""
    # Get login credentials from request
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400
        
    # Check required fields
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Email and password are required'
        }), 400
        
    # Find user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401
        
    # Check password
    if not auth_service.verify_password(user.password_hash, password):
        logger.warning(f"Failed login attempt for user {email}")
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401
        
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user {email}")
        return jsonify({
            'success': False,
            'message': 'Account is inactive or suspended'
        }), 401
    
    # Get permissions for user (based on role)
    permissions = ['read:basic', 'write:basic']
    if user.is_admin:  # Using the property we defined in the User model
        permissions.extend(['read:admin', 'write:admin'])
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    
    # Generate access token
    access_token = auth_service.generate_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        is_admin=user.is_admin,
        permissions=permissions
    )
    
    # Generate refresh token
    refresh_token = auth_service.generate_refresh_token(user_id=user.id)
    
    # Return tokens
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': auth_service.token_expiry,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.name,  # Use name as username
                'is_admin': user.is_admin,
                'tenant_id': user.tenant_id,
                'role': user.role
            }
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Generate a new access token using a refresh token"""
    # Get refresh token from request
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400
        
    # Check required fields
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({
            'success': False,
            'message': 'Refresh token is required'
        }), 400
        
    # Generate new access token
    new_access_token = auth_service.refresh_access_token(refresh_token)
    if not new_access_token:
        return jsonify({
            'success': False,
            'message': 'Invalid or expired refresh token'
        }), 401
        
    # Return new access token
    return jsonify({
        'success': True,
        'message': 'Token refreshed successfully',
        'data': {
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': auth_service.token_expiry
        }
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    # Get registration data from request
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400
        
    # Check required fields
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    if not email or not username or not password:
        return jsonify({
            'success': False,
            'message': 'Email, username, and password are required'
        }), 400
        
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered'
        }), 400
        
    if User.query.filter_by(name=username).first():
        return jsonify({
            'success': False,
            'message': 'Username already taken'
        }), 400
        
    # Hash password
    password_hash = auth_service.hash_password(password)
    
    # Create new user
    # For test/development users, default to tenant_id=1 
    # In production, this would be set based on tenant context or registration flow
    user = User(
        name=username,  # Use name field instead of username
        email=email,
        password_hash=password_hash,
        tenant_id=1,  # Default tenant_id for testing
        role='user',  # Default role
        status='active',  # Default status
        email_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Save to database
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error creating user'
        }), 500
        
    # Generate access token
    access_token = auth_service.generate_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        is_admin=user.is_admin
    )
    
    # Generate refresh token
    refresh_token = auth_service.generate_refresh_token(user_id=user.id)
    
    # Return tokens
    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': auth_service.token_expiry,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.name,  # Use name field as username
                'tenant_id': user.tenant_id,
                'role': user.role
            }
        }
    }), 201

@auth_bp.route('/logout', methods=['POST'])
@auth_service.require_auth()
def logout():
    """Log out a user by revoking their tokens"""
    # Get token ID from request payload
    if not hasattr(g, 'jwt_payload') or not g.jwt_payload:
        return jsonify({
            'success': False,
            'message': 'No valid token found'
        }), 400
        
    token_id = g.jwt_payload.get('jti')
    if not token_id:
        return jsonify({
            'success': False,
            'message': 'Invalid token format'
        }), 400
        
    # Revoke token
    auth_service.revoke_token(token_id, reason='User logout')
    
    # Revoke refresh tokens for user (optional, would require a more complex implementation)
    # This would require tracking which refresh tokens are associated with a user
    
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    })

@auth_bp.route('/me', methods=['GET'])
@auth_service.require_auth()
def get_current_user():
    """Get information about the currently authenticated user"""
    # Get user ID from token
    user_id = g.current_user.get('sub')
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 400
        
    # Find user
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
        
    # Return user information
    return jsonify({
        'success': True,
        'data': {
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.name,  # Use name as username
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'tenant_id': user.tenant_id,
                'role': user.role,
                'email_verified': user.email_verified,
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'permissions': g.current_user.get('permissions', [])
            }
        }
    })

@auth_bp.route('/token/verify', methods=['POST'])
def verify_token():
    """Verify if a token is valid"""
    # Get token from request
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400
        
    # Check required fields
    token = data.get('token')
    if not token:
        return jsonify({
            'success': False,
            'message': 'Token is required'
        }), 400
        
    # Verify token
    payload = auth_service.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid or expired token'
        }), 401
        
    # Return token information
    return jsonify({
        'success': True,
        'message': 'Token is valid',
        'data': {
            'token_info': {
                'expires_at': datetime.fromtimestamp(payload.get('exp')).isoformat(),
                'user_id': payload.get('sub'),
                'is_admin': payload.get('is_admin', False),
                'tenant_id': payload.get('tenant_id')
            }
        }
    })

# Register blueprint with app
def register_auth_routes(app):
    """Register authentication routes with the app"""
    # Exempt authentication routes from CSRF protection
    from flask_wtf.csrf import CSRFProtect
    csrf = app.extensions.get('csrf')
    
    if csrf:
        csrf.exempt(auth_bp)
        logger.info("Authentication routes exempted from CSRF protection")
    else:
        logger.warning("CSRF protection not initialized, cannot exempt auth routes")
    
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered")