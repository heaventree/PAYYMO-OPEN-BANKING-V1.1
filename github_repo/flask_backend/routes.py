import os
import json
import time
import logging
from datetime import datetime, timedelta
from flask import request, jsonify, render_template, abort, session, redirect, url_for
from flask_backend.app import app, db
from flask_backend.models import (
    LicenseKey, LicenseVerification, Transaction, InvoiceMatch,
    WhmcsInstance, BankConnection, ApiLog, StripeConnection, StripePayment
)
from flask_backend.services.gocardless_service_updated import GoCardlessService
from flask_backend.services.license_service import LicenseService
from flask_backend.services.invoice_matching_service import InvoiceMatchingService
from flask_backend.services.stripe_service import StripeService
from flask_backend.utils.error_handler import handle_error, APIError
from flask_backend.utils.logger import log_api_request
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

@app.before_request
def log_request():
    """Log all incoming API requests"""
    if request.path.startswith('/api/'):
        log_api_request(request)

# ============= API Endpoints =============

@app.route('/api/license/verify', methods=['POST'])
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
        
        # Verify the license
        result = license_service.verify_license(
            license_key=license_key, 
            domain=domain,
            ip_address=request.remote_addr,
            system_info=system_info
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/license/info', methods=['POST'])
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
        
        # Get license info
        result = license_service.get_license_info(
            license_key=license_key, 
            domain=domain
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/gocardless/auth', methods=['POST'])
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

@app.route('/dashboard')
def dashboard():
    """Main dashboard route"""
    try:
        admin_session = session.get('admin_logged_in', False)
        tenant_id = session.get('tenant_id')
        
        # For development mode, auto-authenticate
        session['authenticated'] = True
        
        # Try to get dashboard statistics
        stats = {}
        
        # Get dashboard stats from the shared function
        try:
            from flask_backend.routes_steex import get_dashboard_stats
            stats_data = get_dashboard_stats()
            if stats_data and stats_data.get('status') == 'success':
                stats = stats_data
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            stats = {
                'transactions': {'total': 0, 'total_amount': 0, 'month': {'count': 0, 'amount': 0}},
                'bank_connections': {'total': 0, 'active': 0},
                'matches': {'total': 0, 'confirmed': 0, 'pending': 0},
                'stripe_connections': {'total': 0, 'active': 0},
                'stripe_payments': {'total': 0, 'total_amount': 0}
            }
        
        # Get recent transactions for the dashboard
        recent_transactions = []
        bank_connections = []
        stripe_connections = []
        
        if tenant_id:
            # Get bank connections for this tenant
            bank_connections = BankConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
            
            # Get bank IDs
            bank_ids = [conn.bank_id for conn in bank_connections]
            
            # Get transactions
            if bank_ids:
                recent_transactions = Transaction.query.filter(
                    Transaction.bank_id.in_(bank_ids)
                ).order_by(
                    Transaction.transaction_date.desc()
                ).limit(10).all()
            
            # Get Stripe connections for the dashboard
            stripe_connections = StripeConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
                
        return render_template(
            'dashboard/dashboard.html',
            admin_session=admin_session,
            tenant_id=tenant_id,
            stats=stats,
            recent_transactions=recent_transactions,
            bank_connections=bank_connections,
            stripe_connections=stripe_connections
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        # Create empty data structures to prevent template errors
        return render_template(
            'dashboard/dashboard.html', 
            error=str(e),
            admin_session=False,
            tenant_id=None,
            stats={
                'transactions': {'total': 0, 'total_amount': 0, 'month': {'count': 0, 'amount': 0}},
                'bank_connections': {'total': 0, 'active': 0},
                'matches': {'total': 0, 'confirmed': 0, 'pending': 0},
                'stripe_connections': {'total': 0, 'active': 0},
                'stripe_payments': {'total': 0, 'total_amount': 0}
            },
            recent_transactions=[],
            bank_connections=[],
            stripe_connections=[]
        )

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

@app.route('/dashboard-redesign')
def dashboard_redesign():
    """New dashboard with standalone container structure"""
    # Auto-authenticate for development
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
            'dashboard_redesign.html',
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
            recent_transactions=recent_transactions,
            recent_stripe_payments=recent_stripe_payments,
            now=now,
            day_delta=day_delta
        )
    except Exception as e:
        logger.error(f"Error rendering redesigned dashboard: {str(e)}")
        return render_template('dashboard_redesign.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Very basic authentication - replace with proper auth in production
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_username and password == admin_password:
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out from the admin dashboard"""
    session.pop('authenticated', None)
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

@app.route('/')
def index():
    """Root route that provides theme selection"""
    from flask import render_template_string
    html = """
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payymo - Dashboard Selection</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --bs-body-color: #e3e2e7;
                --bs-body-bg: #1a1c24;
            }
            .card {
                border-radius: 1rem;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .btn {
                border-radius: 2rem;
                padding: 0.6rem 1.5rem;
                font-weight: 500;
            }
        </style>
    </head>
    <body class="bg-dark">
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1>Payymo Dashboard</h1>
                <p class="lead text-light opacity-75">Select the dashboard version you'd like to use</p>
            </div>
            
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card bg-dark border-primary mb-4">
                        <div class="card-body text-center p-4">
                            <div class="mb-4">
                                <i class="fas fa-gem fa-3x text-primary mb-3"></i>
                                <h2 class="card-title mb-2">NobleUI</h2>
                                <p class="card-text text-light opacity-75">Modern premium theme with beautiful UI</p>
                            </div>
                            <a href="{{ url_for('nobleui_dashboard') }}" class="btn btn-primary w-100">Open NobleUI Dashboard</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card bg-dark border-info mb-4">
                        <div class="card-body text-center p-4">
                            <div class="mb-4">
                                <i class="fas fa-tachometer-alt fa-3x text-info mb-3"></i>
                                <h2 class="card-title mb-2">Bootstrap 5</h2>
                                <p class="card-text text-light opacity-75">Clean Bootstrap 5 dashboard</p>
                            </div>
                            <a href="{{ url_for('dashboard') }}" class="btn btn-info w-100">Open Bootstrap Dashboard</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card bg-dark border-success">
                        <div class="card-body text-center p-4">
                            <div class="mb-4">
                                <i class="fas fa-code fa-3x text-success mb-3"></i>
                                <h2 class="card-title mb-2">Original</h2>
                                <p class="card-text text-light opacity-75">Previous dashboard implementation</p>
                            </div>
                            <a href="{{ url_for('steex_dashboard') }}" class="btn btn-success w-100">Open Original Dashboard</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/nobleui-dashboard')
def nobleui_dashboard():
    """NobleUI themed dashboard"""
    try:
        admin_session = session.get('admin_logged_in', False)
        tenant_id = session.get('tenant_id')
        
        # For development mode, auto-authenticate
        session['authenticated'] = True
        
        # Try to get dashboard statistics
        stats = {}
        
        # Get dashboard stats from the shared function
        try:
            from flask_backend.routes_steex import get_dashboard_stats
            stats_data = get_dashboard_stats()
            if stats_data and stats_data.get('status') == 'success':
                stats = stats_data
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            stats = {
                'transactions': {'total': 0, 'total_amount': 0, 'month': {'count': 0, 'amount': 0}},
                'bank_connections': {'total': 0, 'active': 0},
                'matches': {'total': 0, 'confirmed': 0, 'pending': 0},
                'stripe_connections': {'total': 0, 'active': 0},
                'stripe_payments': {'total': 0, 'total_amount': 0}
            }
        
        # Get recent transactions for the dashboard
        recent_transactions = []
        bank_connections = []
        stripe_connections = []
        
        # Chart data for transaction history
        chart_data = {
            'amounts': [],
            'dates': []
        }
        
        if tenant_id:
            # Get bank connections for this tenant
            bank_connections = BankConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
            
            # Get bank IDs
            bank_ids = [conn.bank_id for conn in bank_connections]
            
            # Get transactions
            if bank_ids:
                recent_transactions = Transaction.query.filter(
                    Transaction.bank_id.in_(bank_ids)
                ).order_by(
                    Transaction.transaction_date.desc()
                ).limit(10).all()
                
                # Get transaction data for last 6 months for chart
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)  # Last 6 months
                
                # Query transactions by month for chart
                monthly_transactions = db.session.query(
                    db.func.sum(Transaction.amount), 
                    db.func.strftime('%Y-%m', Transaction.transaction_date)
                ).filter(
                    Transaction.bank_id.in_(bank_ids),
                    Transaction.transaction_date.between(start_date, end_date)
                ).group_by(
                    db.func.strftime('%Y-%m', Transaction.transaction_date)
                ).order_by(
                    db.func.strftime('%Y-%m', Transaction.transaction_date)
                ).all()
                
                # Format chart data
                if monthly_transactions:
                    for amount, date_str in monthly_transactions:
                        try:
                            # Convert to month name (e.g., "Jan", "Feb")
                            date_obj = datetime.strptime(date_str, '%Y-%m')
                            month_name = date_obj.strftime('%b')
                            
                            chart_data['amounts'].append(abs(float(amount or 0)))
                            chart_data['dates'].append(month_name)
                        except Exception as e:
                            logger.error(f"Error formatting chart data: {str(e)}")
            
            # Get Stripe connections for the dashboard
            stripe_connections = StripeConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
                
        return render_template(
            'dashboard/nobleui_dashboard.html',
            admin_session=admin_session,
            tenant_id=tenant_id,
            stats=stats,
            recent_transactions=recent_transactions,
            bank_connections=bank_connections,
            stripe_connections=stripe_connections,
            chart_data=chart_data
        )
    except Exception as e:
        logger.error(f"Error rendering NobleUI dashboard: {str(e)}")
        # Create empty data structures to prevent template errors
        return render_template(
            'dashboard/nobleui_dashboard.html', 
            error=str(e),
            admin_session=False,
            tenant_id=None,
            stats={
                'transactions': {'total': 0, 'total_amount': 0, 'month': {'count': 0, 'amount': 0}},
                'bank_connections': {'total': 0, 'active': 0},
                'matches': {'total': 0, 'confirmed': 0, 'pending': 0},
                'stripe_connections': {'total': 0, 'active': 0},
                'stripe_payments': {'total': 0, 'total_amount': 0}
            },
            recent_transactions=[],
            bank_connections=[],
            stripe_connections=[],
            chart_data={'amounts': [], 'dates': []}
        )

@app.route('/api/ai-assistant', methods=['POST'])
def ai_assistant_api():
    """API endpoint for AI Assistant interaction"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        tenant_id = session.get('tenant_id')
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
            
        # Get relevant data for AI context
        stats = {}
        recent_transactions = []
        unmatched_count = 0
        
        try:
            # Get dashboard stats
            from flask_backend.routes_steex import get_dashboard_stats
            stats_data = get_dashboard_stats()
            if stats_data and stats_data.get('status') == 'success':
                stats = stats_data
                
            # Get recent transactions and unmatched count if tenant_id available
            if tenant_id:
                # Get bank connections
                bank_connections = BankConnection.query.filter_by(
                    whmcs_instance_id=tenant_id
                ).all()
                
                bank_ids = [conn.bank_id for conn in bank_connections]
                
                if bank_ids:
                    # Recent transactions
                    recent_transactions = Transaction.query.filter(
                        Transaction.bank_id.in_(bank_ids)
                    ).order_by(
                        Transaction.transaction_date.desc()
                    ).limit(5).all()
                    
                    # Count unmatched transactions
                    from flask_backend.models.financial import StandardizedTransaction, InvoiceMatch
                    
                    # Get all transaction IDs
                    all_transaction_ids = [t.id for t in StandardizedTransaction.query.filter_by(
                        tenant_id=tenant_id
                    ).all()]
                    
                    # Get matched transaction IDs
                    matched_transaction_ids = [m.transaction_id for m in InvoiceMatch.query.filter(
                        InvoiceMatch.transaction_id.in_(all_transaction_ids)
                    ).all()]
                    
                    # Calculate unmatched count
                    unmatched_count = len(all_transaction_ids) - len(matched_transaction_ids)
        except Exception as e:
            logger.error(f"Error preparing AI context data: {str(e)}")
        
        # Process user query and generate response
        response_text = ""
        
        # Simple pattern matching for demo - in production, this would call a more advanced AI model
        if "unmatched" in user_message.lower():
            response_text = f"You currently have {unmatched_count} unmatched transactions. Would you like me to help you review them?"
        
        elif "invoicing status" in user_message.lower():
            if stats and 'matches' in stats:
                confirmed = stats['matches'].get('confirmed', 0)
                pending = stats['matches'].get('pending', 0)
                total = stats['matches'].get('total', 0)
                response_text = f"Your invoicing status: {confirmed} confirmed matches, {pending} pending matches out of {total} total matches."
            else:
                response_text = "I couldn't retrieve your invoicing status at the moment."
        
        elif "transaction patterns" in user_message.lower() or "analyze" in user_message.lower():
            if recent_transactions:
                amounts = [t.amount for t in recent_transactions]
                avg_amount = sum(amounts) / len(amounts) if amounts else 0
                response_text = f"Based on your recent transactions, your average transaction amount is £{abs(avg_amount):.2f}. "
                
                # Add more insights
                if stats and 'transactions' in stats and stats['transactions'].get('month', {}).get('count', 0) > 0:
                    month_count = stats['transactions']['month']['count']
                    response_text += f"You've had {month_count} transactions this month. "
                
                response_text += "Would you like a more detailed analysis of your transaction patterns?"
            else:
                response_text = "I don't have enough transaction data to analyze patterns yet."
        
        elif "optimization" in user_message.lower() or "tips" in user_message.lower():
            response_text = "Here are some optimization tips based on your financial data:\n\n"
            
            if unmatched_count > 0:
                response_text += f"1. You have {unmatched_count} unmatched transactions. Consider reviewing these to improve your invoice matching.\n\n"
            
            if stats and 'bank_connections' in stats and stats['bank_connections'].get('total', 0) < 2:
                response_text += "2. Consider connecting additional bank accounts to get a more complete picture of your finances.\n\n"
            
            response_text += "3. Set up automatic matching rules to save time on manual invoice reconciliation."
        
        else:
            # Default response
            response_text = "I'm your Payymo AI Assistant. I can help you with financial insights, transaction analysis, and optimization tips. What would you like to know about your financial data?"
        
        return jsonify({
            'status': 'success',
            'response': response_text
        })
    
    except Exception as e:
        logger.error(f"Error in AI Assistant API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }), 500
