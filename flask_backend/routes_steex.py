"""
Steex Dashboard Routes
This module contains all routes related to the Steex-themed dashboard
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_backend.app import app
from flask_backend.models import (
    LicenseKey, WhmcsInstance, BankConnection, Transaction, 
    InvoiceMatch, StripeConnection, StripePayment, StripeInvoiceMatch
)
from flask_backend.utils.error_handler import APIError, handle_error

# Set up logging
logger = logging.getLogger(__name__)

def get_dashboard_stats():
    """Get statistics for the dashboard"""
    try:
        # Check if tenant_id is in session
        tenant_id = session.get('tenant_id')
        if not tenant_id:
            return {
                'status': 'no_tenant',
                'message': 'No tenant selected'
            }
        
        # Get WHMCS instance details
        whmcs_instance = WhmcsInstance.query.filter_by(id=tenant_id).first()
        if not whmcs_instance:
            return {
                'status': 'error',
                'message': 'Tenant not found'
            }
        
        # Get license details
        license_key = None
        if whmcs_instance.license_key:
            license_key = LicenseKey.query.filter_by(
                key=whmcs_instance.license_key
            ).first()
        
        # Bank connections
        bank_connections = BankConnection.query.filter_by(
            whmcs_instance_id=tenant_id
        ).all()
        
        active_bank_connections = [b for b in bank_connections if b.status == 'active']
        
        # Transaction data
        bank_ids = [conn.bank_id for conn in bank_connections]
        transactions = Transaction.query.filter(
            Transaction.bank_id.in_(bank_ids)
        ).all()
        
        # Calculate transaction statistics
        total_transactions = len(transactions)
        total_amount = sum(tx.amount for tx in transactions)
        
        # Calculate today's, this week's, and this month's transactions
        today = datetime.utcnow().date()
        start_of_week = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
        
        today_tx = [tx for tx in transactions if tx.transaction_date.date() == today]
        today_amount = sum(tx.amount for tx in today_tx)
        
        week_tx = [tx for tx in transactions if tx.transaction_date.date() >= datetime.strptime(start_of_week, '%Y-%m-%d').date()]
        week_amount = sum(tx.amount for tx in week_tx)
        
        month_tx = [tx for tx in transactions if tx.transaction_date.date() >= datetime.strptime(start_of_month, '%Y-%m-%d').date()]
        month_amount = sum(tx.amount for tx in month_tx)
        
        # Invoice match data
        all_matches = 0
        confirmed_matches = 0
        
        for tx in transactions:
            tx_matches = InvoiceMatch.query.filter_by(transaction_id=tx.id).all()
            all_matches += len(tx_matches)
            confirmed_matches += len([m for m in tx_matches if m.status == 'approved'])
        
        # Stripe connections
        stripe_connections = StripeConnection.query.filter_by(
            whmcs_instance_id=tenant_id
        ).all()
        
        active_stripe_connections = [s for s in stripe_connections if s.status == 'active']
        
        # Stripe payment data
        stripe_connection_ids = [conn.id for conn in stripe_connections]
        stripe_payments = []
        if stripe_connection_ids:
            stripe_payments = StripePayment.query.filter(
                StripePayment.stripe_connection_id.in_(stripe_connection_ids)
            ).all()
        
        # Calculate Stripe payment statistics
        total_stripe_payments = len(stripe_payments)
        total_stripe_amount = sum(payment.amount for payment in stripe_payments)
        
        # Return compiled stats
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'tenant_name': whmcs_instance.domain,
            'license': license_key.key if license_key else None,
            'license_status': license_key.status if license_key else 'none',
            'bank_connections': {
                'total': len(bank_connections),
                'active': len(active_bank_connections)
            },
            'transactions': {
                'total': total_transactions,
                'total_amount': total_amount,
                'today': {
                    'count': len(today_tx),
                    'amount': today_amount
                },
                'week': {
                    'count': len(week_tx),
                    'amount': week_amount
                },
                'month': {
                    'count': len(month_tx),
                    'amount': month_amount
                }
            },
            'matches': {
                'total': all_matches,
                'confirmed': confirmed_matches,
                'pending': all_matches - confirmed_matches
            },
            'stripe_connections': {
                'total': len(stripe_connections),
                'active': len(active_stripe_connections)
            },
            'stripe_payments': {
                'total': total_stripe_payments,
                'total_amount': total_stripe_amount
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@app.route('/steex-dashboard')
def steex_dashboard():
    """Steex-themed dashboard with the new UI"""
    try:
        admin_session = session.get('admin_logged_in', False)
        tenant_id = session.get('tenant_id')
        
        # For development mode, auto-authenticate
        session['authenticated'] = True
        
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Get recent transactions for the dashboard
        recent_transactions = []
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
        
        # Get bank connections for the dashboard
        bank_connections = []
        if tenant_id:
            bank_connections = BankConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
        
        # Get Stripe connections for the dashboard
        stripe_connections = []
        if tenant_id:
            stripe_connections = StripeConnection.query.filter_by(
                whmcs_instance_id=tenant_id
            ).all()
        
        # Calculate financial summary data
        total_transactions = stats.get('transactions', {}).get('total', 0)
        total_amount = stats.get('transactions', {}).get('total_amount', 0)
        
        # Get current month's transactions for the chart
        monthly_transactions = []
        if tenant_id and bank_connections:
            today = datetime.utcnow()
            start_of_month = datetime(today.year, today.month, 1)
            
            # Get bank IDs
            bank_ids = [conn.bank_id for conn in bank_connections]
            
            # Get transactions
            if bank_ids:
                monthly_transactions = Transaction.query.filter(
                    Transaction.bank_id.in_(bank_ids),
                    Transaction.transaction_date >= start_of_month
                ).order_by(Transaction.transaction_date).all()
        
        # Format chart data
        chart_data = {
            'dates': [],
            'amounts': []
        }
        
        # Group by day for the chart
        if monthly_transactions:
            today = datetime.utcnow()
            current_date = datetime(today.year, today.month, 1)
            
            while current_date.date() <= today.date():
                chart_data['dates'].append(current_date.strftime('%d %b'))
                
                # Sum transactions for this day
                daily_sum = sum(
                    tx.amount for tx in monthly_transactions 
                    if tx.transaction_date.date() == current_date.date()
                )
                chart_data['amounts'].append(daily_sum)
                
                current_date += timedelta(days=1)
        
        return render_template(
            'steex/dashboard.html',
            admin_session=admin_session,
            stats=stats,
            recent_transactions=recent_transactions,
            bank_connections=bank_connections,
            stripe_connections=stripe_connections,
            total_transactions=total_transactions,
            total_amount=total_amount,
            chart_data=chart_data
        )
    except Exception as e:
        logger.error(f"Error rendering Steex dashboard: {str(e)}")
        return render_template('steex/dashboard.html', error=str(e))