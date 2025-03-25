"""
Fresh Dashboard Routes
This module contains all routes related to the fresh Steex-themed dashboard implementation.
"""

import os
import logging
from flask import render_template, redirect, url_for, session
from flask_backend.app import app

# Set up logging
logger = logging.getLogger(__name__)

@app.route('/fresh-dashboard')
def fresh_dashboard():
    """Fresh Steex-themed dashboard with the new UI"""
    try:
        admin_session = session.get('admin_logged_in', False)
        tenant_id = session.get('tenant_id')
        
        # For development mode, auto-authenticate
        session['authenticated'] = True
        
        # Get dashboard statistics
        from flask_backend.routes_steex import get_dashboard_stats
        stats = get_dashboard_stats()
        
        # Get recent transactions for the dashboard
        recent_transactions = []
        if tenant_id:
            from flask_backend.models import BankConnection, Transaction
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
        
        # Get bank connections for the dashboard
        bank_connections = []
        if tenant_id:
            from flask_backend.models import BankConnection
            bank_connections = BankConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
        
        # Get Stripe connections for the dashboard
        stripe_connections = []
        if tenant_id:
            from flask_backend.models import StripeConnection
            stripe_connections = StripeConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
                
        return render_template(
            'steex_fresh/dashboard.html',
            admin_session=admin_session,
            tenant_id=tenant_id,
            stats=stats,
            recent_transactions=recent_transactions,
            bank_connections=bank_connections,
            stripe_connections=stripe_connections
        )
    except Exception as e:
        logger.error(f"Error rendering Fresh dashboard: {str(e)}")
        return render_template('steex_fresh/dashboard.html', error=str(e))