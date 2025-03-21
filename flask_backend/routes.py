import os
import json
import time
import logging
from datetime import datetime
from flask import request, jsonify, render_template, abort, session, redirect, url_for
from flask_backend.app import app, db
from flask_backend.models import (
    LicenseKey, LicenseVerification, Transaction, InvoiceMatch,
    WhmcsInstance, BankConnection, ApiLog
)
from flask_backend.services.gocardless_service import GoCardlessService
from flask_backend.services.license_service import LicenseService
from flask_backend.services.invoice_matching_service import InvoiceMatchingService
from flask_backend.utils.error_handler import handle_error, APIError
from flask_backend.utils.logger import log_api_request

# Initialize services
license_service = LicenseService()
gocardless_service = GoCardlessService()
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
    except Exception as e:
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

# ============= Admin Dashboard =============

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Simple authentication check - in a real app, use a proper auth system
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Get some stats for the dashboard
    try:
        license_count = LicenseKey.query.count()
        active_licenses = LicenseKey.query.filter_by(status='active').count()
        whmcs_instances = WhmcsInstance.query.count()
        bank_connections = BankConnection.query.count()
        transactions = Transaction.query.count()
        matches = InvoiceMatch.query.count()
        
        recent_verifications = LicenseVerification.query.order_by(
            LicenseVerification.verified_at.desc()
        ).limit(10).all()
        
        recent_transactions = Transaction.query.order_by(
            Transaction.transaction_date.desc()
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
                'matches': matches
            },
            recent_verifications=recent_verifications,
            recent_transactions=recent_transactions,
            now=now,
            day_delta=day_delta
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return render_template('dashboard.html', error=str(e))

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

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check database connectivity
    try:
        db.session.execute('SELECT 1')
        db_status = "OK"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = f"Error: {str(e)}"
    
    # Check GoCardless API connectivity
    try:
        gocardless_status = "OK" if gocardless_service.check_health() else "Error"
    except Exception as e:
        logger.error(f"GoCardless health check failed: {str(e)}")
        gocardless_status = f"Error: {str(e)}"
    
    # Return health status
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "gocardless_api": gocardless_status
        }
    })
