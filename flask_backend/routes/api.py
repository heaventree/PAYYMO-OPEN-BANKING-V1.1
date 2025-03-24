"""
API routes for the multi-tenant SaaS application
These routes handle REST API endpoints for the multi-tenant system
"""
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from flask_backend.app import db
from flask_backend.models.auth import User, ApiKey
from flask_backend.models.integrations import Integration, IntegrationType
from flask_backend.models.financial import StandardizedTransaction, StandardizedInvoice, InvoiceTransaction
from flask_backend.utils.tenant_middleware import tenant_header_required

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API key authentication middleware
def api_key_required(f):
    """Decorator to require API key authentication"""
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'Authentication required',
                'message': 'API key is required'
            }), 401
            
        # Check if API key is valid
        key = ApiKey.query.filter_by(key=api_key).first()
        
        if not key or not key.is_active:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or inactive'
            }), 401
            
        # Store API key in request context
        g.api_key = key
        
        # If this is a tenant-specific API key, set tenant context
        if key.tenant_id:
            g.tenant_id = key.tenant_id
            g.tenant = key.tenant
            
        return f(*args, **kwargs)
    
    return decorated_function

# Health check endpoint (no authentication required)
@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

# Authenticated endpoints
@api_bp.route('/account')
@api_key_required
def account():
    """Get account information"""
    key = g.api_key
    
    # If tenant-specific key
    if key.tenant_id:
        tenant = key.tenant
        return jsonify({
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'created_at': tenant.created_at.isoformat()
            },
            'api_key': {
                'id': key.id,
                'name': key.name,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None
            }
        })
    else:
        # Platform-level key
        user = key.user
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            },
            'api_key': {
                'id': key.id,
                'name': key.name,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None
            }
        })

# Tenant-specific endpoints
@api_bp.route('/transactions')
@api_key_required
@tenant_header_required
def transactions():
    """Get transactions for a tenant"""
    tenant_id = g.tenant_id
    
    # Default to last 30 days
    date_from = request.args.get('date_from', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        return jsonify({
            'error': 'Invalid date format',
            'message': 'Date format should be YYYY-MM-DD'
        }), 400
    
    # Get transactions with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    transactions = StandardizedTransaction.query.filter_by(tenant_id=tenant_id)
    
    # Apply date filters if provided
    if date_from:
        transactions = transactions.filter(StandardizedTransaction.transaction_date >= date_from)
    if date_to:
        transactions = transactions.filter(StandardizedTransaction.transaction_date <= date_to)
        
    # Apply source filter if provided
    source = request.args.get('source')
    if source:
        transactions = transactions.filter(StandardizedTransaction.source == source)
        
    # Apply status filter if provided
    status = request.args.get('status')
    if status:
        transactions = transactions.filter(StandardizedTransaction.status == status)
        
    # Order by transaction date (newest first)
    transactions = transactions.order_by(StandardizedTransaction.transaction_date.desc())
    
    # Paginate results
    paginated = transactions.paginate(page=page, per_page=per_page)
    
    # Prepare response
    response = {
        'transactions': [],
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total_pages': paginated.pages,
            'total_items': paginated.total
        }
    }
    
    # Format transactions
    for transaction in paginated.items:
        response['transactions'].append({
            'id': transaction.id,
            'source': transaction.source,
            'source_id': transaction.source_id,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status,
            'description': transaction.description,
            'reference': transaction.reference,
            'transaction_date': transaction.transaction_date.isoformat(),
            'created_at': transaction.created_at.isoformat()
        })
    
    return jsonify(response)

@api_bp.route('/invoices')
@api_key_required
@tenant_header_required
def invoices():
    """Get invoices for a tenant"""
    tenant_id = g.tenant_id
    
    # Default to last 30 days
    date_from = request.args.get('date_from', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        return jsonify({
            'error': 'Invalid date format',
            'message': 'Date format should be YYYY-MM-DD'
        }), 400
    
    # Get invoices with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    invoices = StandardizedInvoice.query.filter_by(tenant_id=tenant_id)
    
    # Apply date filters if provided
    if date_from:
        invoices = invoices.filter(StandardizedInvoice.invoice_date >= date_from)
    if date_to:
        invoices = invoices.filter(StandardizedInvoice.invoice_date <= date_to)
        
    # Apply source filter if provided
    source = request.args.get('source')
    if source:
        invoices = invoices.filter(StandardizedInvoice.source == source)
        
    # Apply status filter if provided
    status = request.args.get('status')
    if status:
        invoices = invoices.filter(StandardizedInvoice.status == status)
        
    # Order by invoice date (newest first)
    invoices = invoices.order_by(StandardizedInvoice.invoice_date.desc())
    
    # Paginate results
    paginated = invoices.paginate(page=page, per_page=per_page)
    
    # Prepare response
    response = {
        'invoices': [],
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total_pages': paginated.pages,
            'total_items': paginated.total
        }
    }
    
    # Format invoices
    for invoice in paginated.items:
        response['invoices'].append({
            'id': invoice.id,
            'source': invoice.source,
            'source_id': invoice.source_id,
            'number': invoice.number,
            'total': float(invoice.total),
            'balance': float(invoice.balance),
            'currency': invoice.currency,
            'status': invoice.status,
            'customer_id': invoice.customer_id,
            'customer_name': invoice.customer_name,
            'customer_email': invoice.customer_email,
            'invoice_date': invoice.invoice_date.isoformat(),
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'created_at': invoice.created_at.isoformat()
        })
    
    return jsonify(response)

@api_bp.route('/integrations')
@api_key_required
@tenant_header_required
def integrations():
    """Get integrations for a tenant"""
    tenant_id = g.tenant_id
    
    # Get all integrations for the tenant
    tenant_integrations = Integration.query.filter_by(tenant_id=tenant_id).all()
    
    # Prepare response
    response = {
        'integrations': []
    }
    
    # Format integrations
    for integration in tenant_integrations:
        # Don't include sensitive credentials
        config = integration.config.copy() if integration.config else {}
        if 'credentials' in config:
            del config['credentials']
            
        response['integrations'].append({
            'id': integration.id,
            'type': integration.type,
            'name': integration.name,
            'status': integration.status,
            'config': config,
            'created_at': integration.created_at.isoformat(),
            'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None
        })
    
    return jsonify(response)

@api_bp.route('/transactions/<int:transaction_id>/matches')
@api_key_required
@tenant_header_required
def transaction_matches(transaction_id):
    """Get invoice matches for a transaction"""
    tenant_id = g.tenant_id
    
    # Get transaction
    transaction = StandardizedTransaction.query.filter_by(
        id=transaction_id,
        tenant_id=tenant_id
    ).first()
    
    if not transaction:
        return jsonify({
            'error': 'Transaction not found',
            'message': f'No transaction found with ID {transaction_id}'
        }), 404
    
    # Get matches
    matches = InvoiceTransaction.query.filter_by(
        transaction_id=transaction_id,
        tenant_id=tenant_id
    ).all()
    
    # Prepare response
    response = {
        'transaction': {
            'id': transaction.id,
            'source': transaction.source,
            'source_id': transaction.source_id,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status,
            'description': transaction.description,
            'reference': transaction.reference,
            'transaction_date': transaction.transaction_date.isoformat()
        },
        'matches': []
    }
    
    # Format matches
    for match in matches:
        invoice = match.invoice
        response['matches'].append({
            'id': match.id,
            'invoice_id': match.invoice_id,
            'amount_applied': float(match.amount_applied),
            'currency': match.currency,
            'status': match.status,
            'confidence': float(match.confidence),
            'match_reason': match.match_reason,
            'created_at': match.created_at.isoformat(),
            'invoice': {
                'id': invoice.id,
                'source': invoice.source,
                'source_id': invoice.source_id,
                'number': invoice.number,
                'total': float(invoice.total),
                'balance': float(invoice.balance),
                'currency': invoice.currency,
                'status': invoice.status,
                'customer_name': invoice.customer_name,
                'invoice_date': invoice.invoice_date.isoformat()
            }
        })
    
    return jsonify(response)

@api_bp.route('/dashboard/stats')
@api_key_required
@tenant_header_required
def dashboard_stats():
    """Get dashboard statistics for a tenant"""
    tenant_id = g.tenant_id
    
    # Time ranges
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Transaction stats
    new_transactions_today = StandardizedTransaction.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedTransaction.transaction_date >= today).count()
        
    new_transactions_yesterday = StandardizedTransaction.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedTransaction.transaction_date >= yesterday) \
        .filter(StandardizedTransaction.transaction_date < today).count()
        
    new_transactions_7_days = StandardizedTransaction.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedTransaction.transaction_date >= last_7_days).count()
        
    new_transactions_30_days = StandardizedTransaction.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedTransaction.transaction_date >= last_30_days).count()
        
    # Invoice stats
    new_invoices_today = StandardizedInvoice.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedInvoice.invoice_date >= today).count()
        
    new_invoices_yesterday = StandardizedInvoice.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedInvoice.invoice_date >= yesterday) \
        .filter(StandardizedInvoice.invoice_date < today).count()
        
    new_invoices_7_days = StandardizedInvoice.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedInvoice.invoice_date >= last_7_days).count()
        
    new_invoices_30_days = StandardizedInvoice.query.filter_by(tenant_id=tenant_id) \
        .filter(StandardizedInvoice.invoice_date >= last_30_days).count()
        
    # Match stats
    matches_today = InvoiceTransaction.query.filter_by(tenant_id=tenant_id) \
        .filter(InvoiceTransaction.created_at >= today).count()
        
    pending_matches = InvoiceTransaction.query.filter_by(
        tenant_id=tenant_id,
        status='pending'
    ).count()
    
    # Balance stats
    # Sum all transaction amounts for the tenant
    # This is a simple approximation, real balance would need more complex accounting logic
    balance_query = StandardizedTransaction.query.filter_by(tenant_id=tenant_id)
    total_transaction_amount = sum([t.amount for t in balance_query.all()]) or 0
    
    return jsonify({
        'transactions': {
            'today': new_transactions_today,
            'yesterday': new_transactions_yesterday,
            'last_7_days': new_transactions_7_days,
            'last_30_days': new_transactions_30_days
        },
        'invoices': {
            'today': new_invoices_today,
            'yesterday': new_invoices_yesterday,
            'last_7_days': new_invoices_7_days,
            'last_30_days': new_invoices_30_days
        },
        'matches': {
            'today': matches_today,
            'pending': pending_matches
        },
        'balance': {
            'total': float(total_transaction_amount)
        }
    })
