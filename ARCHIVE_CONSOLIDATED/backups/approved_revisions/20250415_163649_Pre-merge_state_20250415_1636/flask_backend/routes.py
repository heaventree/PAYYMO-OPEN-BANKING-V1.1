import os
import json
import time
import logging
from datetime import datetime, timedelta
from flask import request, jsonify, render_template, abort, session, redirect, url_for
from flask_backend.app import app, db, limiter
from werkzeug.security import generate_password_hash, check_password_hash
from flask_backend.models import (
    LicenseKey, LicenseVerification, Transaction, InvoiceMatch,
    WhmcsInstance, BankConnection, ApiLog, StripeConnection, StripePayment
)
from flask_backend.services.gocardless_service_updated import GoCardlessService
from flask_backend.services.license_service import LicenseService
from flask_backend.services.invoice_matching_service import InvoiceMatchingService
from flask_backend.services.stripe_service import StripeService
from flask_backend.utils.error_handler import APIError, handle_error
from flask_backend.utils.gocardless_errors import (
    GoCardlessError, GoCardlessAuthError, GoCardlessBankConnectionError,
    GoCardlessTransactionError, GoCardlessWebhookError, handle_gocardless_error
)

# Initialize services
license_service = LicenseService()
gocardless_service = GoCardlessService()
stripe_service = StripeService()
invoice_matching_service = InvoiceMatchingService()

# Logger
logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_all_exceptions(error):
    """Global exception handler that returns formatted JSON responses"""
    return handle_error(error)

# API requests are now logged by middleware in utils/logger.py

# ============= API Endpoints =============

@app.route('/api/license/verify', methods=['POST'])
@limiter.limit("20 per minute")  # Limit API calls to prevent abuse
def verify_license():
    """Verify a license key for a WHMCS instance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        license_key = data.get('license_key')
        domain = data.get('domain')
        system_info = data.get('system_info', {})
        
        if not license_key or not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Log verification attempt
        logger.info(f"License verification attempt for domain: {domain}, IP: {request.remote_addr}")
        
        # Verify the license
        result = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr,
            system_info=system_info
        )
        
        # Add headers for cache control
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        return handle_error(e)

@app.route('/api/license/info', methods=['POST'])
@limiter.limit("10 per minute")  # Limit API calls to prevent abuse
def license_info():
    """Get detailed information about a license"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        
        if not license_key or not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Log the request
        logger.info(f"License info request for domain: {domain}, IP: {request.remote_addr}")
        
        # Get license info
        result = license_service.get_license_info(
            license_key=license_key, 
            domain=domain
        )
        
        # Add cache control headers
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        
        return response
    except Exception as e:
        return handle_error(e)

@app.route('/api/gocardless/auth', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limiting for GoCardless auth
def gocardless_auth():
    """Get GoCardless authorization URL"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        redirect_uri = data.get('redirect_uri')
        
        if not license_key or not domain or not redirect_uri:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Get GoCardless auth URL
        auth_url = gocardless_service.get_authorization_url(
            domain=domain,
            redirect_uri=redirect_uri
        )
        
        return jsonify({"auth_url": auth_url})
    except GoCardlessError as e:
        # Handle specific GoCardless errors with detailed information
        return handle_gocardless_error(e)
    except Exception as e:
        return handle_error(e)

@app.route('/api/gocardless/callback', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limiting for GoCardless OAuth callback
def gocardless_callback():
    """Handle GoCardless OAuth callback"""
    try:
        # Can be GET or POST depending on the GoCardless configuration
        if request.method == 'POST':
            data = request.get_json()
            code = data.get('code')
            state = data.get('state')
        else:
            code = request.args.get('code')
            state = request.args.get('state')
        
        if not code or not state:
            raise APIError("Missing required parameters", status_code=400)
        
        # Process the callback
        result = gocardless_service.process_callback(code, state)
        
        return jsonify(result)
    except GoCardlessAuthError as e:
        # Handle OAuth-specific errors
        logger.error(f"GoCardless OAuth error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessBankConnectionError as e:
        # Handle bank connection errors
        logger.error(f"GoCardless bank connection error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessError as e:
        # Handle other GoCardless errors
        return handle_gocardless_error(e)
    except Exception as e:
        return handle_error(e)

@app.route('/api/gocardless/banks', methods=['GET'])
def get_available_banks():
    """Get a list of available banks from GoCardless"""
    try:
        country = request.args.get('country')
        limit = request.args.get('limit', 50, type=int)
        
        banks = gocardless_service.get_available_banks(country=country, limit=limit)
        
        return jsonify({
            'success': True,
            'banks': banks
        })
    except GoCardlessBankConnectionError as e:
        # Handle bank connection errors
        logger.error(f"GoCardless bank connection error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessError as e:
        # Handle other GoCardless errors
        return handle_gocardless_error(e)
    except Exception as e:
        return handle_error(e)

@app.route('/api/gocardless/webhook', methods=['POST'])
def gocardless_webhook():
    """
    Handle GoCardless webhooks with certificate verification
    
    GoCardless sends webhooks with a client certificate that we need to verify
    to ensure the webhook is authentic.
    """
    try:
        # Log the incoming webhook
        logger.info("Received GoCardless webhook")
        
        # Get client certificate data if present
        client_cert = request.environ.get('SSL_CLIENT_CERT')
        
        # Verify the webhook using the client certificate
        if not gocardless_service.verify_webhook_certificate(client_cert):
            logger.warning("Invalid GoCardless webhook certificate")
            raise GoCardlessWebhookError(
                message="Invalid webhook certificate", 
                error_type="cert_verification_failed", 
                http_status=403
            )
        
        # Parse the webhook payload
        webhook_data = request.get_json()
        if not webhook_data:
            raise GoCardlessWebhookError(
                message="Invalid webhook payload - missing JSON data", 
                error_type="invalid_payload", 
                http_status=400
            )
        
        # Validate required webhook fields
        if not webhook_data.get('event_type') or not webhook_data.get('resource_type'):
            raise GoCardlessWebhookError(
                message="Invalid webhook format - missing required fields", 
                error_type="invalid_format", 
                http_status=400
            )
        
        # Process the webhook data
        result = gocardless_service.process_webhook(webhook_data)
        
        return jsonify({"status": "success", "message": "Webhook processed successfully"})
    except GoCardlessWebhookError as e:
        # Handle webhook-specific errors
        logger.error(f"GoCardless webhook error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessError as e:
        # Handle other GoCardless errors
        return handle_gocardless_error(e)
    except Exception as e:
        logger.error(f"Error processing GoCardless webhook: {str(e)}")
        return handle_error(e)

@app.route('/api/transactions/fetch', methods=['POST'])
@limiter.limit("30 per minute")  # Higher limit for transaction fetching as it's a common operation
def fetch_transactions():
    """Fetch transactions from GoCardless for a specific bank account"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')
        from_date = data.get('from_date')
        to_date = data.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        
        if not license_key or not domain or not account_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Fetch transactions
        transactions = gocardless_service.fetch_transactions(
            domain=domain,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )
        
        return jsonify({"transactions": transactions})
    except GoCardlessAuthError as e:
        # Handle authentication errors (e.g., expired tokens)
        logger.error(f"GoCardless authentication error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessTransactionError as e:
        # Handle transaction-specific errors
        logger.error(f"GoCardless transaction error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessBankConnectionError as e:
        # Handle bank connection errors
        logger.error(f"GoCardless bank connection error: {e.message}")
        return handle_gocardless_error(e)
    except GoCardlessError as e:
        # Handle other GoCardless errors
        return handle_gocardless_error(e)
    except Exception as e:
        return handle_error(e)

@app.route('/api/transactions/match', methods=['POST'])
@limiter.limit("20 per minute")  # Limit match transaction requests
def match_transaction():
    """Match a transaction to an invoice"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        transaction_id = data.get('transaction_id')
        
        if not license_key or not domain or not transaction_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Find matches for the transaction
        matches = invoice_matching_service.find_matches(
            domain=domain,
            transaction_id=transaction_id
        )
        
        return jsonify({"matches": matches})
    except Exception as e:
        return handle_error(e)

@app.route('/api/match/apply', methods=['POST'])
@limiter.limit("15 per minute")  # Rate limiting for applying matches
def apply_match():
    """Apply a match between a transaction and an invoice"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        match_id = data.get('match_id')
        
        if not license_key or not domain or not match_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Apply the match
        result = invoice_matching_service.apply_match(
            domain=domain,
            match_id=match_id
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/match/reject', methods=['POST'])
@limiter.limit("15 per minute")  # Rate limiting for rejecting matches
def reject_match():
    """Reject a match between a transaction and an invoice"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        match_id = data.get('match_id')
        
        if not license_key or not domain or not match_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Reject the match
        result = invoice_matching_service.reject_match(
            domain=domain,
            match_id=match_id
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

# ============= Stripe API Endpoints =============

@app.route('/api/stripe/auth', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limiting for Stripe auth endpoint
def stripe_auth():
    """Get Stripe authorization URL"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        redirect_uri = data.get('redirect_uri')
        
        if not license_key or not domain or not redirect_uri:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Get Stripe auth URL
        auth_url = stripe_service.get_authorization_url(
            domain=domain,
            redirect_uri=redirect_uri
        )
        
        return jsonify({"auth_url": auth_url})
    except Exception as e:
        return handle_error(e)

@app.route('/api/stripe/callback', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limiting for Stripe OAuth callback
def stripe_callback():
    """Handle Stripe OAuth callback"""
    try:
        # Can be GET or POST depending on the Stripe configuration
        if request.method == 'POST':
            data = request.get_json()
            code = data.get('code')
            state = data.get('state')
        else:
            code = request.args.get('code')
            state = request.args.get('state')
        
        if not code or not state:
            raise APIError("Missing required parameters", status_code=400)
        
        # Process the callback
        result = stripe_service.process_callback(code, state)
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/stripe/transactions/fetch', methods=['POST'])
@limiter.limit("30 per minute")  # Higher limit for fetching Stripe transaction data
def fetch_stripe_transactions():
    """Fetch transaction records from Stripe for a specific account"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')
        from_date = data.get('from_date')
        to_date = data.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        
        if not license_key or not domain or not account_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Fetch payments
        payments = stripe_service.fetch_payments(
            domain=domain,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )
        
        return jsonify({"payments": payments})
    except Exception as e:
        return handle_error(e)

@app.route('/api/stripe/balance', methods=['POST'])
@limiter.limit("30 per minute")  # Rate limiting for Stripe balance endpoint
def get_stripe_balance():
    """Get Stripe account balance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')
        
        if not license_key or not domain or not account_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Get balance
        balance = stripe_service.get_account_balance(
            domain=domain,
            account_id=account_id
        )
        
        return jsonify({"balance": balance})
    except Exception as e:
        return handle_error(e)

# ============= Admin Dashboard =============

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # For development mode, auto-authenticate
    session['authenticated'] = True
    
    # Simple authentication check - in a real app, use a proper auth system
    # if not session.get('authenticated'):
    #     return redirect(url_for('login'))
    
    # Get some stats for the dashboard
    try:
        license_count = LicenseKey.query.count()
        active_licenses = LicenseKey.query.filter_by(status='active').count()
        whmcs_instances = WhmcsInstance.query.count()
        bank_connections = BankConnection.query.count()
        transactions = Transaction.query.count()
        matches = InvoiceMatch.query.count()
        
        # Stripe stats
        stripe_connections = StripeConnection.query.count()
        stripe_payments = StripePayment.query.count()
        
        recent_verifications = LicenseVerification.query.order_by(
            LicenseVerification.verified_at.desc()
        ).limit(10).all()
        
        recent_transactions = Transaction.query.order_by(
            Transaction.transaction_date.desc()
        ).limit(10).all()
        
        # Get recent Stripe payments
        recent_stripe_payments = StripePayment.query.order_by(
            StripePayment.payment_date.desc()
        ).limit(10).all()
        
        # Get current date for charts
        now = datetime.now()
        day_delta = timedelta(days=1)
        
        return render_template(
            'dashboard.html',
            stats={
                'license_count': license_count,
                'active_licenses': active_licenses,
                'whmcs_instances': whmcs_instances,
                'bank_connections': bank_connections,
                'transactions': transactions,
                'matches': matches,
                'stripe_connections': stripe_connections,
                'stripe_payments': stripe_payments
            },
            recent_verifications=recent_verifications,
            recent_transactions=recent_transactions,
            recent_stripe_payments=recent_stripe_payments,
            now=now,
            day_delta=day_delta
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return render_template('dashboard.html', error=str(e))

@app.route('/dashboard2')
def dashboard2():
    """Redesigned dashboard page with consistent styling"""
    # For development mode, auto-authenticate
    session['authenticated'] = True
    
    # Get some stats for the dashboard
    try:
        license_count = LicenseKey.query.count()
        active_licenses = LicenseKey.query.filter_by(status='active').count()
        whmcs_instances = WhmcsInstance.query.count()
        bank_connections = BankConnection.query.count()
        transactions = Transaction.query.count()
        matches = InvoiceMatch.query.count()
        
        # Stripe stats
        stripe_connections = StripeConnection.query.count()
        stripe_payments = StripePayment.query.count()
        
        recent_verifications = LicenseVerification.query.order_by(
            LicenseVerification.verified_at.desc()
        ).limit(10).all()
        
        recent_transactions = Transaction.query.order_by(
            Transaction.transaction_date.desc()
        ).limit(10).all()
        
        # Get recent Stripe payments
        recent_stripe_payments = StripePayment.query.order_by(
            StripePayment.payment_date.desc()
        ).limit(10).all()
        
        # Get current date for charts
        now = datetime.now()
        day_delta = timedelta(days=1)
        
        return render_template(
            'dashboard2.html',
            stats={
                'license_count': license_count,
                'active_licenses': active_licenses,
                'whmcs_instances': whmcs_instances,
                'bank_connections': bank_connections,
                'transactions': transactions,
                'matches': matches,
                'stripe_connections': stripe_connections,
                'stripe_payments': stripe_payments
            },
            recent_verifications=recent_verifications,
            recent_transactions=recent_transactions,
            recent_stripe_payments=recent_stripe_payments,
            now=now,
            day_delta=day_delta
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return render_template('dashboard2.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Limit login attempts to prevent brute force attacks
def login():
    """Admin login page with enhanced security"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # More secure authentication with password hashing
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        
        # In production, this would be a pre-hashed password stored in a database
        # For now, we're getting a password from environment but with better security
        stored_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        plain_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        # If no hash is available, use the plain password (but hash it for comparison)
        if not stored_password_hash:
            # This simulates a stored hash for demonstration
            stored_password_hash = generate_password_hash(plain_password)
        
        # Perform the login verification with secure hash comparison
        # No timing attack vulnerability as check_password_hash is time-constant
        if username == admin_username and check_password_hash(stored_password_hash, password):
            # Add timestamp and IP for session activity tracking
            session['authenticated'] = True
            session['login_time'] = datetime.now().isoformat()
            session['login_ip'] = request.remote_addr
            session.permanent = True  # Use the permanent session lifetime from config
            
            # Log successful login
            logger.info(f"Successful login for user {username} from {request.remote_addr}")
            return redirect(url_for('dashboard'))
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for user {username} from {request.remote_addr}")
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out from the admin dashboard with enhanced security"""
    # Log the logout
    if session.get('authenticated'):
        logger.info(f"User logged out from {request.remote_addr}")
    
    # Clear all session data, not just the authenticated flag
    session.clear()
    
    # Set a flash message for the next request
    return redirect(url_for('login'))

# ============= Health Check =============

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    # Check database connectivity
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = "OK"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = f"Error: {str(e)}"
    
    # Check GoCardless API connectivity
    try:
        gocardless_health = gocardless_service.check_health()
        gocardless_status = "OK" if gocardless_health else "Error"
    except Exception as e:
        logger.error(f"GoCardless health check failed: {str(e)}")
        gocardless_status = f"Error: {str(e)}"
    
    # Check Stripe API connectivity
    try:
        stripe_health = stripe_service.check_health()
        stripe_status = "OK" if stripe_health else "Error"
    except Exception as e:
        logger.error(f"Stripe health check failed: {str(e)}")
        stripe_status = f"Error: {str(e)}"
    
    # Return health status
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "gocardless_api": gocardless_status,
            "stripe_api": stripe_status
        }
    })
    
@app.route('/api/testing/generate-stripe-data', methods=['POST'])
def generate_stripe_test_data():
    """Generate test data for Stripe payments"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        license_key = data.get('license_key')
        domain = data.get('domain')
        account_id = data.get('account_id')  # Optional
        num_payments = data.get('num_payments', 10)
        
        if not license_key or not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify license first
        license_valid = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr
        )
        
        if not license_valid.get('valid', False):
            raise APIError("Invalid license", status_code=403)
        
        # Generate test data
        result = stripe_service.generate_test_data(
            domain=domain,
            account_id=account_id,
            num_payments=num_payments
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)
