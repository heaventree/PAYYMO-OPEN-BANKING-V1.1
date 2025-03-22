"""
Stripe hosted checkout integration for the Payymo service.
This module provides a simple implementation for redirecting to Stripe's hosted checkout page.
"""
import os
import stripe
from flask import Blueprint, redirect, request, jsonify, current_app
from flask_backend.utils.error_handler import handle_error, APIError

# Initialize Blueprint
checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

# Get Stripe API key from environment
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@checkout_bp.route('/create-session', methods=['POST'])
def create_checkout_session():
    """
    Create a Stripe Checkout Session and redirect to the Stripe-hosted checkout page.
    
    Request body:
    {
        "price_id": "price_1234",    # The Stripe Price ID
        "quantity": 1,               # Number of items
        "success_url": "https://example.com/success",  # URL to redirect after successful payment
        "cancel_url": "https://example.com/cancel"     # URL to redirect if user cancels
    }
    """
    try:
        # Check if Stripe API key is configured
        if not stripe.api_key:
            raise APIError("Stripe API key not configured", status_code=500)
        
        # Get request data
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Get required fields
        price_id = data.get('price_id')
        success_url = data.get('success_url')
        cancel_url = data.get('cancel_url')
        quantity = data.get('quantity', 1)
        
        if not price_id or not success_url or not cancel_url:
            raise APIError("Missing required fields", status_code=400)
        
        # Create the checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': quantity,
                },
            ],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            automatic_tax={'enabled': True},
        )
        
        # Return the checkout URL
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url
        })
    except Exception as stripe_error:
        if hasattr(stripe_error, 'http_status'):
            # Handle Stripe-specific errors
            return handle_error(APIError(str(stripe_error), status_code=stripe_error.http_status))
        # Handle other Stripe errors
        return handle_error(APIError(str(stripe_error), status_code=400))
    except Exception as e:
        # Handle other errors
        return handle_error(e)

@checkout_bp.route('/redirect-to-checkout', methods=['POST'])
def redirect_to_checkout():
    """
    Create a Stripe Checkout Session and redirect to the Stripe-hosted checkout page.
    Similar to create-checkout-session but returns a redirect instead of JSON.
    """
    try:
        # Check if Stripe API key is configured
        if not stripe.api_key:
            raise APIError("Stripe API key not configured", status_code=500)
        
        # Get request data
        data = request.get_json()
        
        if not data:
            raise APIError("No data provided", status_code=400)
        
        # Get required fields
        price_id = data.get('price_id')
        success_url = data.get('success_url')
        cancel_url = data.get('cancel_url')
        quantity = data.get('quantity', 1)
        
        if not price_id or not success_url or not cancel_url:
            raise APIError("Missing required fields", status_code=400)
        
        # Create the checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': quantity,
                },
            ],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            automatic_tax={'enabled': True},
        )
        
        # Redirect to the checkout page
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        # Handle errors
        return handle_error(e)

@checkout_bp.route('/success', methods=['GET'])
def checkout_success():
    """Handle successful checkout"""
    return jsonify({
        'success': True,
        'message': 'Payment successful!'
    })

@checkout_bp.route('/cancel', methods=['GET'])
def checkout_cancel():
    """Handle canceled checkout"""
    return jsonify({
        'success': False,
        'message': 'Payment canceled'
    })