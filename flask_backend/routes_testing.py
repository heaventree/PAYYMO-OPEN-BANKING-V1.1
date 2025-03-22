"""
WHMCS Testing API Routes
Endpoints for testing WHMCS integration and providing diagnostic tools
These routes are used only for testing and debugging purposes
"""
import json
import logging
from datetime import datetime
from flask import request, jsonify, render_template, abort, session, redirect, url_for
from flask_backend.app import app, db
from flask_backend.models import WhmcsInstance, ApiLog
from flask_backend.services.whmcs_test_service import WhmcsTestService
from flask_backend.utils.error_handler import handle_error, APIError

# Initialize testing service
whmcs_test_service = WhmcsTestService()

# Logger
logger = logging.getLogger(__name__)

# ============= WHMCS Testing API Endpoints =============

@app.route('/api/testing/register', methods=['POST'])
def register_test_instance():
    """Register a WHMCS instance for testing"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        api_identifier = data.get('api_identifier')
        api_secret = data.get('api_secret')
        
        # Optional fields
        admin_user = data.get('admin_user')
        license_key = data.get('license_key')
        
        if not domain or not api_identifier or not api_secret:
            raise APIError("Missing required fields", status_code=400)
        
        # Register the test instance
        result = whmcs_test_service.register_test_instance(
            domain=domain,
            api_identifier=api_identifier,
            api_secret=api_secret,
            admin_user=admin_user,
            license_key=license_key
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/verify-connection', methods=['POST'])
def verify_test_connection():
    """Verify connection to a WHMCS instance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        api_identifier = data.get('api_identifier')
        api_secret = data.get('api_secret')
        
        if not domain or not api_identifier or not api_secret:
            raise APIError("Missing required fields", status_code=400)
        
        # Verify the connection
        result = whmcs_test_service.verify_connection(
            domain=domain,
            api_identifier=api_identifier,
            api_secret=api_secret
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/webhook-test', methods=['POST'])
def test_webhook():
    """Test webhook functionality"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        
        if not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Test the webhook
        result = whmcs_test_service.test_webhook(domain=domain)
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/log-error', methods=['POST'])
def log_error():
    """Log an error from a WHMCS instance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        error_type = data.get('error_type')
        error_message = data.get('error_message')
        
        # Optional fields
        error_context = data.get('error_context')
        
        if not domain or not error_type or not error_message:
            raise APIError("Missing required fields", status_code=400)
        
        # Log the error
        result = whmcs_test_service.log_error(
            domain=domain,
            error_type=error_type,
            error_message=error_message,
            error_context=error_context
        )
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/status', methods=['POST'])
def get_test_status():
    """Get status information for a WHMCS instance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        
        if not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Get the status
        result = whmcs_test_service.get_status(domain=domain)
        
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

# ============= WHMCS Module Callback Endpoints =============

@app.route('/api/testing/module-installed', methods=['POST'])
def module_installed():
    """Callback for when the WHMCS module is installed"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        license_key = data.get('license_key')
        version = data.get('version')
        
        if not domain or not license_key:
            raise APIError("Missing required fields", status_code=400)
        
        # Log the installation
        logger.info(f"Module installed on {domain} with license {license_key}, version {version}")
        
        # Find the instance
        instance = WhmcsInstance.query.filter_by(domain=domain).first()
        if instance:
            # Update license key if needed
            if instance.license_key != license_key:
                instance.license_key = license_key
            
            # Update last seen
            instance.last_seen = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Module installation recorded",
                "webhook_secret": instance.webhook_secret
            })
        else:
            # Create new instance with a webhook secret
            webhook_secret = whmcs_test_service._generate_webhook_secret(domain)
            
            instance = WhmcsInstance(
                domain=domain,
                license_key=license_key,
                webhook_secret=webhook_secret
            )
            
            db.session.add(instance)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "New module installation recorded",
                "webhook_secret": webhook_secret
            })
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/diagnostic', methods=['POST'])
def run_diagnostic():
    """Run diagnostic tests for a WHMCS instance"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        
        if not domain:
            raise APIError("Missing required fields", status_code=400)
        
        # Find the instance
        instance = WhmcsInstance.query.filter_by(domain=domain).first()
        if not instance:
            raise APIError("WHMCS instance not found", status_code=404)
        
        # Run basic diagnostics
        tests = []
        
        # Test 1: Check if API credentials are set
        api_creds_test = {
            "name": "API Credentials",
            "success": bool(instance.api_identifier and instance.api_secret),
            "message": "API credentials are set" if (instance.api_identifier and instance.api_secret) else "API credentials are not set"
        }
        tests.append(api_creds_test)
        
        # Test 2: Check if license key is valid
        license_test = {
            "name": "License Key",
            "success": bool(instance.license_key),
            "message": "License key is set" if instance.license_key else "License key is not set"
        }
        tests.append(license_test)
        
        # Test 3: Check how recently the instance was seen
        last_seen_diff = (datetime.utcnow() - instance.last_seen).total_seconds() / 3600  # hours
        last_seen_test = {
            "name": "Last Seen",
            "success": last_seen_diff < 24,  # Success if seen in the last 24 hours
            "message": f"Last seen {last_seen_diff:.1f} hours ago"
        }
        tests.append(last_seen_test)
        
        # Test 4: Check for bank connections
        bank_test = {
            "name": "Bank Connections",
            "success": len(instance.bank_connections) > 0,
            "message": f"Found {len(instance.bank_connections)} bank connections"
        }
        tests.append(bank_test)
        
        # Test 5: Check for Stripe connections
        stripe_test = {
            "name": "Stripe Connections",
            "success": len(instance.stripe_connections) > 0,
            "message": f"Found {len(instance.stripe_connections)} Stripe connections"
        }
        tests.append(stripe_test)
        
        # Test 6: Check for recent errors
        recent_errors = ApiLog.query.filter(
            ApiLog.endpoint.like(f"{domain}/%"),
            ApiLog.method == "ERROR"
        ).count()
        
        error_test = {
            "name": "Recent Errors",
            "success": recent_errors == 0,
            "message": f"Found {recent_errors} recent errors"
        }
        tests.append(error_test)
        
        return jsonify({
            "success": True,
            "instance_id": instance.id,
            "domain": instance.domain,
            "tests": tests,
            "overall_status": "healthy" if all(t["success"] for t in tests) else "issues_detected"
        })
    except Exception as e:
        return handle_error(e)

# ============= GoCardless CLI Testing Endpoints =============

@app.route('/api/testing/import-transactions', methods=['POST'])
def import_test_transactions():
    """
    Import test transactions from the GoCardless CLI
    
    This endpoint allows importing transactions directly from the GoCardless CLI
    for testing purposes without going through the full OAuth flow.
    
    Example request body:
    {
        "domain": "example.com",
        "transactions": [
            {
                "id": "tr_123456",
                "bank_id": "bank_123",
                "bank_name": "Test Bank",
                "account_id": "acc_123",
                "account_name": "Test Account",
                "amount": 100.00,
                "currency": "GBP",
                "description": "Test Transaction",
                "reference": "REF123",
                "date": "2025-03-22"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        transactions = data.get('transactions', [])
        
        if not domain or not transactions:
            raise APIError("Missing required fields", status_code=400)
        
        # Find the WHMCS instance
        instance = WhmcsInstance.query.filter_by(domain=domain).first()
        if not instance:
            raise APIError("WHMCS instance not found", status_code=404)
        
        from flask_backend.models import Transaction
        
        # Import the transactions
        imported_count = 0
        for transaction_data in transactions:
            # Check if transaction already exists
            existing = Transaction.query.filter_by(transaction_id=transaction_data['id']).first()
            
            if existing:
                # Skip if already exists
                continue
            
            # Create new transaction record
            transaction = Transaction(
                transaction_id=transaction_data['id'],
                bank_id=transaction_data.get('bank_id', 'test_bank'),
                bank_name=transaction_data.get('bank_name', 'Test Bank'),
                account_id=transaction_data.get('account_id', 'test_account'),
                account_name=transaction_data.get('account_name', 'Test Account'),
                amount=float(transaction_data['amount']),
                currency=transaction_data.get('currency', 'GBP'),
                description=transaction_data.get('description', ''),
                reference=transaction_data.get('reference', ''),
                transaction_date=datetime.strptime(transaction_data['date'], '%Y-%m-%d')
            )
            
            db.session.add(transaction)
            imported_count += 1
        
        db.session.commit()
        
        logger.info(f"Imported {imported_count} test transactions for {domain}")
        
        return jsonify({
            "success": True,
            "message": f"Successfully imported {imported_count} transactions",
            "imported_count": imported_count
        })
    except Exception as e:
        return handle_error(e)

@app.route('/api/testing/simulated-webhook', methods=['POST'])
def simulated_webhook():
    """
    Process a simulated webhook event from the GoCardless CLI
    
    This endpoint simulates a webhook event from GoCardless without requiring
    certificate validation, making it easier to test webhook handling locally.
    
    Example request body:
    {
        "domain": "example.com", 
        "event_type": "transactions.created",
        "resource_id": "tr_123456",
        "payload": {
            "data": {
                "id": "tr_123456",
                "amount": 100.00,
                "description": "Test Payment"
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Required fields
        domain = data.get('domain')
        event_type = data.get('event_type')
        resource_id = data.get('resource_id')
        payload = data.get('payload')
        
        if not domain or not event_type or not resource_id:
            raise APIError("Missing required fields", status_code=400)
        
        # Find the WHMCS instance
        instance = WhmcsInstance.query.filter_by(domain=domain).first()
        if not instance:
            raise APIError("WHMCS instance not found", status_code=404)
        
        # Log the webhook
        logger.info(f"Received simulated webhook for {domain}: {event_type} - {resource_id}")
        
        # Process the webhook
        from flask_backend.services.gocardless_service import GoCardlessService
        gocardless_service = GoCardlessService()
        
        # Skip certificate validation since this is a simulated webhook
        process_result = gocardless_service.process_webhook(
            payload or {
                "event_type": event_type,
                "resource_id": resource_id,
                "data": {
                    "id": resource_id
                }
            }
        )
        
        return jsonify({
            "success": True,
            "message": "Successfully processed simulated webhook",
            "process_result": process_result
        })
    except Exception as e:
        return handle_error(e)

# ============= Testing Dashboard Pages =============

@app.route('/testing')
def testing_dashboard():
    """Testing dashboard page"""
    # Simple authentication check - in a real app, use a proper auth system
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Get all WHMCS instances
    instances = WhmcsInstance.query.all()
    
    # Get recent errors
    recent_errors = ApiLog.query.filter(
        ApiLog.method == "ERROR"
    ).order_by(ApiLog.created_at.desc()).limit(10).all()
    
    from datetime import datetime
    return render_template(
        'testing_dashboard.html',
        instances=instances,
        recent_errors=recent_errors,
        now=datetime.utcnow()
    )

@app.route('/testing/instance/<int:instance_id>')
def testing_instance_detail(instance_id):
    """Testing instance detail page"""
    # Simple authentication check - in a real app, use a proper auth system
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Get the instance
    instance = WhmcsInstance.query.get_or_404(instance_id)
    
    # Get instance-specific errors
    instance_errors = ApiLog.query.filter(
        ApiLog.endpoint.like(f"{instance.domain}/%"),
        ApiLog.method == "ERROR"
    ).order_by(ApiLog.created_at.desc()).limit(20).all()
    
    # Get all API interactions for this instance
    api_logs = ApiLog.query.filter(
        ApiLog.endpoint.like(f"%{instance.domain}%")
    ).order_by(ApiLog.created_at.desc()).limit(50).all()
    
    from datetime import datetime
    return render_template(
        'testing_instance_detail.html',
        instance=instance,
        instance_errors=instance_errors,
        api_logs=api_logs,
        now=datetime.utcnow()
    )