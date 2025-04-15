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
from flask_backend.app import limiter
from flask_backend.utils.validators import (
    is_valid_email, is_valid_password, is_valid_username, 
    is_valid_string, sanitize_string
)
from flask_backend.utils.security_errors import (
    ValidationError, AuthenticationError, AuthorizationError,
    RateLimitError, TokenError
)

# Logger
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter rate limit for login attempts to prevent brute force
def login():
    """Log in a user and return access and refresh tokens"""
    try:
        # Get login credentials from request
        data = request.get_json()
        if not data:
            raise ValidationError("Invalid request data")
            
        # Extract fields
        email = data.get('email')
        password = data.get('password')
        
        # Comprehensive validation
        validation_errors = {}
        
        # Validate email format
        is_email_valid, email_error = is_valid_email(email)
        if not is_email_valid:
            validation_errors['email'] = email_error
        
        # Validate password presence (basic validation for login)
        if not password:
            validation_errors['password'] = "Password is required"
            
        # If any validation failed, raise error with all errors
        if validation_errors:
            raise ValidationError("Validation failed", errors=validation_errors)
        
        # Sanitize email for database lookup
        sanitized_email = sanitize_string(email)
        
        # Find user with enhanced security measures
        user = User.query.filter_by(email=sanitized_email).first()
        
        # Handle non-existent user (with same timing as valid user for security)
        if not user:
            # This prevents timing attacks that could reveal if an email exists
            # We should create a method to simulate password comparison time
            auth_service.dummy_password_check()
            # Log attempt with minimal information (first 3 chars only)
            logger.warning(f"Login failed: Email not found ({sanitized_email[:3]}...)")
            raise AuthenticationError(
                "Invalid email or password",
                log_message=f"Login attempt with non-existent email: {sanitized_email}"
            )
            
        # Check password with constant-time comparison
        if not auth_service.verify_password(user.password_hash, password):
            # Log with user ID for auditing but use generic message in response
            logger.warning(f"Login failed: Invalid password for user ID {user.id}")
            raise AuthenticationError(
                "Invalid email or password",
                log_message=f"Failed password attempt for user ID: {user.id}"
            )
            
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user ID {user.id}")
            raise AuthenticationError(
                "Account is inactive or suspended",
                log_message=f"Login attempt for inactive user: {user.id}"
            )
            
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
    
    except (ValidationError, AuthenticationError) as e:
        # These exceptions will be handled by the error handler
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"Unexpected error in login: {str(e)}")
        raise


@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit("20 per minute")  # Less strict limit for token refresh
def refresh_token():
    """Generate a new access token using a refresh token"""
    try:
        # Get refresh token from request
        data = request.get_json()
        if not data:
            raise ValidationError("Invalid request data")
            
        # Extract refresh token
        refresh_token = data.get('refresh_token')
        
        # Validate refresh token input
        is_token_valid, token_error = is_valid_string(
            refresh_token, 
            field_name="Refresh token", 
            required=True, 
            max_length=4096  # JWT tokens can be quite long
        )
        
        if not is_token_valid:
            raise ValidationError("Invalid refresh token", {"refresh_token": token_error})
        
        # Sanitize token (minimal sanitization since tokens are sensitive)
        refresh_token = refresh_token.strip()
            
        # Generate new access token
        new_access_token = auth_service.refresh_access_token(refresh_token)
        if not new_access_token:
            raise TokenError(
                "Invalid or expired refresh token",
                log_message="Failed to refresh token - invalid or expired"
            )
            
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
        
    except (ValidationError, TokenError) as e:
        # These exceptions will be handled by the error handler
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"Unexpected error in token refresh: {str(e)}")
        raise

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour, 20 per day")  # Strict limits for registration to prevent abuse
def register():
    """Register a new user"""
    # Get registration data from request
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400
        
    # Extract and validate required fields
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    
    # Comprehensive validation
    validation_errors = {}
    
    # Validate email
    is_email_valid, email_error = is_valid_email(email)
    if not is_email_valid:
        validation_errors['email'] = email_error
    
    # Validate username
    is_username_valid, username_error = is_valid_username(username)
    if not is_username_valid:
        validation_errors['username'] = username_error
    
    # Validate password strength
    is_password_valid, password_error = is_valid_password(password)
    if not is_password_valid:
        validation_errors['password'] = password_error
    
    # If any validation failed, return all errors
    if validation_errors:
        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': validation_errors
        }), 400
    
    # Sanitize inputs before database operations
    sanitized_email = sanitize_string(email)
    sanitized_username = sanitize_string(username)
    
    # Check if user already exists
    if User.query.filter_by(email=sanitized_email).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered'
        }), 400
        
    if User.query.filter_by(name=sanitized_username).first():
        return jsonify({
            'success': False,
            'message': 'Username already taken'
        }), 400
        
    # Hash password
    password_hash = auth_service.hash_password(password)
    
    # Create new user with sanitized inputs
    # For test/development users, default to tenant_id=1 
    # In production, this would be set based on tenant context or registration flow
    user = User(
        name=sanitized_username,  # Use sanitized name field instead of username
        email=sanitized_email,    # Use sanitized email
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
    try:
        # Get token ID from request payload
        if not hasattr(g, 'jwt_payload') or not g.jwt_payload:
            raise TokenError("No valid token found", log_message="Logout attempted without valid token")
            
        token_id = g.jwt_payload.get('jti')
        if not token_id:
            raise TokenError("Invalid token format", log_message="Token missing JTI claim during logout")
        
        # Get user ID from token
        user_id = g.jwt_payload.get('sub')
            
        # Revoke token
        revocation_success = auth_service.revoke_token(
            token_id=token_id, 
            reason='User logout', 
            user_id=user_id
        )
        
        if not revocation_success:
            logger.warning(f"Token revocation failed for token ID {token_id}")
            raise TokenError(
                "Failed to revoke token",
                log_message=f"Token revocation failed for user ID {user_id}"
            )
        
        # TODO: In a production system, we would also revoke all refresh tokens for this user
        # This would require tracking which refresh tokens are associated with a user
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        
    except TokenError as e:
        # These exceptions will be handled by the error handler
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"Unexpected error in logout: {str(e)}")
        raise

@auth_bp.route('/me', methods=['GET'])
@auth_service.require_auth()
def get_current_user():
    """Get information about the currently authenticated user"""
    try:
        # Get user ID from token
        user_id = g.current_user.get('sub')
        if not user_id:
            raise TokenError(
                "Invalid token", 
                log_message="Token missing subject claim during user profile request"
            )
            
        # Find user
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found for ID {user_id} from token")
            raise AuthenticationError(
                "User not found",
                log_message=f"User ID from token not found in database: {user_id}"
            )
            
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
        
    except (TokenError, AuthenticationError) as e:
        # These exceptions will be handled by the error handler
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"Unexpected error in user profile retrieval: {str(e)}")
        raise

@auth_bp.route('/token/verify', methods=['POST'])
@limiter.limit("30 per minute")  # Medium rate limit for token verification
def verify_token():
    """Verify if a token is valid"""
    try:
        # Get token from request
        data = request.get_json()
        if not data:
            raise ValidationError("Invalid request data")
            
        # Extract token
        token = data.get('token')
        
        # Validate token input
        is_token_valid, token_error = is_valid_string(
            token, 
            field_name="Token", 
            required=True, 
            max_length=4096  # JWT tokens can be quite long
        )
        
        if not is_token_valid:
            raise ValidationError("Invalid token format", {"token": token_error})
            
        # Sanitize token (minimal sanitization since tokens are sensitive)
        token = token.strip()
            
        # Verify token
        payload = auth_service.verify_token(token)
        if not payload:
            raise TokenError(
                "Invalid or expired token",
                log_message="Token verification failed - invalid or expired"
            )
            
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
        
    except (ValidationError, TokenError) as e:
        # These exceptions will be handled by the error handler
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"Unexpected error in token verification: {str(e)}")
        raise

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