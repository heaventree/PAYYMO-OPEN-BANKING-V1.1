"""
Dashboard routes for the multi-tenant SaaS application
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, g
from flask_backend.utils.tenant_middleware import tenant_from_subdomain, current_tenant
from flask_backend.models.auth import User, UserRole
from flask_backend.models.integrations import Integration, IntegrationSync
from flask_backend.models.financial import StandardizedTransaction, StandardizedInvoice, InvoiceTransaction

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')

@dashboard_bp.route('/')
@tenant_from_subdomain
def index():
    """Main dashboard page for the multi-tenant application"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    # Get dashboard stats
    stats = get_tenant_dashboard_stats(g.tenant.id)
    
    # Get recent transactions
    recent_transactions = get_recent_transactions(g.tenant.id, limit=5)
    
    # Get recent invoices
    recent_invoices = get_recent_invoices(g.tenant.id, limit=5)
    
    # Get integration statuses
    integrations = get_tenant_integrations(g.tenant.id)
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        recent_transactions=recent_transactions,
        recent_invoices=recent_invoices,
        integrations=integrations
    )

@dashboard_bp.route('/transactions')
@tenant_from_subdomain
def transactions():
    """Transactions page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    # Default to last 30 days
    date_from = request.args.get('date_from', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Get transactions with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    transactions = StandardizedTransaction.query.filter_by(tenant_id=g.tenant.id)
    
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
    paginated_transactions = transactions.paginate(page=page, per_page=per_page)
    
    return render_template(
        'dashboard/transactions.html',
        transactions=paginated_transactions,
        date_from=date_from,
        date_to=date_to,
        source=source,
        status=status
    )

@dashboard_bp.route('/invoices')
@tenant_from_subdomain
def invoices():
    """Invoices page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    # Default to last 30 days
    date_from = request.args.get('date_from', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Get invoices with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    invoices = StandardizedInvoice.query.filter_by(tenant_id=g.tenant.id)
    
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
    paginated_invoices = invoices.paginate(page=page, per_page=per_page)
    
    return render_template(
        'dashboard/invoices.html',
        invoices=paginated_invoices,
        date_from=date_from,
        date_to=date_to,
        source=source,
        status=status
    )

@dashboard_bp.route('/integrations')
@tenant_from_subdomain
def integrations():
    """Integrations management page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    # Get all integrations for the tenant
    tenant_integrations = Integration.query.filter_by(tenant_id=g.tenant.id).all()
    
    return render_template(
        'dashboard/integrations.html',
        integrations=tenant_integrations
    )

@dashboard_bp.route('/settings')
@tenant_from_subdomain
def settings():
    """Tenant settings page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    return render_template(
        'dashboard/settings.html',
        tenant=g.tenant
    )

@dashboard_bp.route('/users')
@tenant_from_subdomain
def users():
    """User management page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    # Check if user has admin permissions
    user = User.query.get(session['user_id'])
    if not user or user.role != UserRole.ADMIN.value:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('dashboard.index'))
        
    # Get all users for this tenant
    tenant_users = User.query.filter_by(tenant_id=g.tenant.id).all()
    
    return render_template(
        'dashboard/users.html',
        users=tenant_users
    )

@dashboard_bp.route('/dashboard-redesign')
@tenant_from_subdomain
def redesign():
    """New dashboard with standalone container structure"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # If no tenant context, redirect to tenant selection page
    if not hasattr(g, 'tenant'):
        return redirect(url_for('auth.select_tenant'))
        
    try:
        # Get dashboard stats
        stats = get_tenant_dashboard_stats(g.tenant.id)
        
        # Get recent transactions
        recent_transactions = get_recent_transactions(g.tenant.id, limit=5)
        
        # Get recent invoices
        recent_invoices = get_recent_invoices(g.tenant.id, limit=5)
        
        # Get integration statuses
        integrations = get_tenant_integrations(g.tenant.id)
        
        # Current tenant
        tenant = g.tenant
        
        return render_template(
            'dashboard_redesign.html',
            stats=stats,
            recent_transactions=recent_transactions,
            recent_invoices=recent_invoices,
            integrations=integrations,
            tenant=tenant
        )
    except Exception as e:
        logger.error(f"Error rendering redesigned dashboard: {str(e)}")
        return render_template('dashboard_redesign.html', error=str(e))

# Helper functions
def get_tenant_dashboard_stats(tenant_id):
    """Get dashboard statistics for a tenant"""
    # Time ranges
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    try:
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
    except Exception as e:
        logger.warning(f"Error getting dashboard stats: {str(e)}")
        # Return default values if there's an error (like missing tables)
        return {
            'new_transactions_today': 0,
            'new_transactions_yesterday': 0,
            'new_transactions_7_days': 0,
            'new_transactions_30_days': 0,
            'new_invoices_today': 0,
            'new_invoices_yesterday': 0,
            'new_invoices_7_days': 0,
            'new_invoices_30_days': 0,
            'matches_today': 0,
            'pending_matches': 0,
            'total_transaction_amount': 0
        }
    
    return {
        'new_transactions_today': new_transactions_today,
        'new_transactions_yesterday': new_transactions_yesterday,
        'new_transactions_7_days': new_transactions_7_days,
        'new_transactions_30_days': new_transactions_30_days,
        'new_invoices_today': new_invoices_today,
        'new_invoices_yesterday': new_invoices_yesterday,
        'new_invoices_7_days': new_invoices_7_days,
        'new_invoices_30_days': new_invoices_30_days,
        'matches_today': matches_today,
        'pending_matches': pending_matches,
        'total_transaction_amount': total_transaction_amount
    }

def get_recent_transactions(tenant_id, limit=5):
    """Get recent transactions for a tenant"""
    try:
        return StandardizedTransaction.query.filter_by(tenant_id=tenant_id) \
            .order_by(StandardizedTransaction.transaction_date.desc()) \
            .limit(limit).all()
    except Exception as e:
        logger.warning(f"Error getting recent transactions: {str(e)}")
        return []

def get_recent_invoices(tenant_id, limit=5):
    """Get recent invoices for a tenant"""
    try:
        return StandardizedInvoice.query.filter_by(tenant_id=tenant_id) \
            .order_by(StandardizedInvoice.invoice_date.desc()) \
            .limit(limit).all()
    except Exception as e:
        logger.warning(f"Error getting recent invoices: {str(e)}")
        return []

def get_tenant_integrations(tenant_id):
    """Get integration statuses for a tenant"""
    try:
        return Integration.query.filter_by(tenant_id=tenant_id).all()
    except Exception as e:
        logger.warning(f"Error getting tenant integrations: {str(e)}")
        return []
