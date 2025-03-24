"""
Authentication routes for the multi-tenant SaaS application
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_backend.app import db
from flask_backend.models.auth import User, UserRole, LoginAttempt, PasswordReset, TenantUser
from flask_backend.models.core import Tenant
from flask_backend.utils.tenant_middleware import tenant_from_subdomain

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@tenant_from_subdomain
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
            
        # Check if this is a tenant-specific login
        if hasattr(g, 'tenant'):
            # Find user for this tenant
            tenant_user = TenantUser.query.join(User).filter(
                User.email == email,
                TenantUser.tenant_id == g.tenant.id
            ).first()
            
            if not tenant_user:
                # Log failed attempt
                log_login_attempt(email, success=False, tenant_id=g.tenant.id)
                
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html')
                
            user = tenant_user.user
        else:
            # Platform-level login
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Log failed attempt
                log_login_attempt(email, success=False)
                
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html')
        
        # Check password
        if check_password_hash(user.password_hash, password):
            # Log successful login
            log_login_attempt(email, success=True, tenant_id=getattr(g, 'tenant_id', None))
            
            # Store user info in session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            # If this is a tenant-specific login, store tenant info
            if hasattr(g, 'tenant'):
                session['tenant_id'] = g.tenant.id
                
                # Redirect to tenant dashboard
                return redirect(url_for('dashboard.index'))
            else:
                # Redirect to tenant selection page (for users with multiple tenants)
                if len(user.tenants) > 1:
                    return redirect(url_for('auth.select_tenant'))
                elif len(user.tenants) == 1:
                    # If user only has one tenant, set it active and redirect to dashboard
                    tenant = user.tenants[0].tenant
                    session['tenant_id'] = tenant.id
                    return redirect(url_for('dashboard.index'))
                else:
                    # User has no tenants, redirect to dashboard or create tenant
                    flash('You do not have access to any tenants. Please contact an administrator.', 'warning')
                    return redirect(url_for('auth.login'))
        else:
            # Log failed attempt
            log_login_attempt(email, success=False, tenant_id=getattr(g, 'tenant_id', None))
            
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
    
    # GET request - show login form
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/select-tenant')
def select_tenant():
    """Tenant selection page for users with multiple tenants"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    # Get all tenants for this user
    tenant_list = Tenant.query.join(TenantUser).filter(
        TenantUser.user_id == user.id
    ).all()
    
    return render_template('auth/select_tenant.html', tenants=tenant_list)

@auth_bp.route('/set-tenant/<int:tenant_id>')
def set_tenant(tenant_id):
    """Set active tenant for the session"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    # Check if user has access to this tenant
    tenant_user = TenantUser.query.filter_by(
        user_id=user.id,
        tenant_id=tenant_id
    ).first()
    
    if not tenant_user:
        flash('You do not have access to this tenant', 'error')
        return redirect(url_for('auth.select_tenant'))
        
    # Set tenant in session
    session['tenant_id'] = tenant_id
    
    # Redirect to dashboard
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email address is required', 'error')
            return render_template('auth/forgot_password.html')
            
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create password reset record
            reset = PasswordReset(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            
            db.session.add(reset)
            db.session.commit()
            
            # TODO: Send reset email
            # This would normally send an email with the reset link
            # For now, just log it
            reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
            logger.info(f"Password reset link for {email}: {reset_link}")
            
        # Always show success message, even if email doesn't exist
        # This prevents email enumeration attacks
        flash('If your email exists in our system, you will receive a password reset link shortly', 'info')
        return redirect(url_for('auth.login'))
        
    # GET request - show forgot password form
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page"""
    # Check if token is valid
    reset = PasswordReset.query.filter_by(token=token).first()
    
    if not reset or reset.is_used or reset.expires_at < datetime.utcnow():
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Password and confirmation are required', 'error')
            return render_template('auth/reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)
            
        # Update user password
        user = User.query.get(reset.user_id)
        user.password_hash = generate_password_hash(password)
        
        # Mark reset token as used
        reset.is_used = True
        reset.used_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Your password has been reset successfully', 'success')
        return redirect(url_for('auth.login'))
        
    # GET request - show reset password form
    return render_template('auth/reset_password.html', token=token)

# Helper functions
def log_login_attempt(email, success, tenant_id=None):
    """Log a login attempt"""
    attempt = LoginAttempt(
        email=email,
        success=success,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        tenant_id=tenant_id
    )
    
    db.session.add(attempt)
    db.session.commit()

def generate_reset_token(length=32):
    """Generate a secure random token for password reset"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
