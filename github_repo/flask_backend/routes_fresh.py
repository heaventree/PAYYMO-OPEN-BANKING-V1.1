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

@app.route('/test-route')
def test_route():
    """A simple test route to verify routing is working"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Route</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body class="bg-dark text-light p-5">
        <div class="container">
            <h1>Test Route Works!</h1>
            <p class="lead">This confirms our routing is functioning correctly.</p>
            <a href="/fresh-dashboard" class="btn btn-primary mt-3">Go to Fresh Dashboard</a>
        </div>
    </body>
    </html>
    """

@app.route('/fresh-dashboard')
def fresh_dashboard():
    """Fresh Steex-themed dashboard with the new UI"""
    try:
        admin_session = session.get('admin_logged_in', False)
        tenant_id = session.get('tenant_id')
        
        # For development mode, auto-authenticate
        session['authenticated'] = True
        
        # Default stats structure
        stats = {
            'transactions': {
                'total': 0,
                'total_amount': 0,
                'month': {
                    'count': 0,
                    'amount': 0
                }
            },
            'bank_connections': {
                'total': 0,
                'active': 0
            },
            'matches': {
                'total': 0,
                'confirmed': 0,
                'pending': 0
            },
            'stripe_connections': {
                'total': 0,
                'active': 0
            },
            'stripe_payments': {
                'total': 0,
                'total_amount': 0
            }
        }
        
        # Try to get dashboard statistics from the main function
        try:
            from flask_backend.routes_steex import get_dashboard_stats
            stats_data = get_dashboard_stats()
            if stats_data and stats_data.get('status') == 'success':
                stats = stats_data
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
        
        # Get recent transactions for the dashboard
        recent_transactions = []
        bank_connections = []
        stripe_connections = []
        
        try:
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
                
                # Get Stripe connections for the dashboard
                from flask_backend.models import StripeConnection
                stripe_connections = StripeConnection.query.filter_by(
                    whmcs_instance_id=tenant_id
                ).all()
        except Exception as e:
            logger.error(f"Error fetching tenant data: {str(e)}")
                
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
        # Create empty data structures to prevent template errors
        return render_template(
            'steex_fresh/dashboard.html', 
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