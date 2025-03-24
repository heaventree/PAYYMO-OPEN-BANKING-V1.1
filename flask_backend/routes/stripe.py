import os
import json
import stripe
from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from flask_backend.utils.tenant_middleware import tenant_required

# Configure Stripe
stripe_exceptions = stripe.error

stripe_bp = Blueprint('stripe', __name__, url_prefix='/stripe')

# Initialize Stripe with the API key from environment variables
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@stripe_bp.route('/connect', methods=['GET'])
@tenant_required
def connect():
    """
    Get the Stripe OAuth URL to connect a Stripe account
    """
    # In a real implementation, we would store and validate this state
    state = f"tenant_{session.get('tenant_id')}"
    
    # Get the current domain
    domain = request.host
    
    # Create the OAuth URL
    oauth_url = stripe.OAuth.authorize_url(
        scope='read_write',
        state=state,
        redirect_uri=f"https://{domain}{url_for('stripe.callback')}"
    )
    
    return jsonify({
        'success': True,
        'oauth_url': oauth_url
    })

@stripe_bp.route('/callback', methods=['GET'])
@tenant_required
def callback():
    """
    Handle the callback from Stripe OAuth
    """
    # Get the authorization code and state from the query parameters
    authorization_code = request.args.get('code')
    state = request.args.get('state')
    
    # Get the current domain
    domain = request.host
    
    # Verify the state (in a real implementation, we would validate this against the stored state)
    expected_state = f"tenant_{session.get('tenant_id')}"
    if state != expected_state:
        return render_template('error.html', error='Invalid state parameter. Please try again.')
    
    try:
        # Exchange the authorization code for an access token
        resp = stripe.OAuth.token(
            grant_type='authorization_code',
            code=authorization_code,
        )
        
        # Access the connected account ID
        connected_account_id = resp['stripe_user_id']
        access_token = resp['access_token']
        
        # Store the connected account information in the database
        # In a real implementation, we would save this to the database
        # and associate it with the current tenant
        
        # Redirect to the dashboard with a success message
        return redirect(url_for('dashboard.index', connection_success=True))
        
    except stripe.error.StripeError as e:
        # Handle any errors
        return render_template('error.html', error=f'Stripe Error: {str(e)}')
    
@stripe_bp.route('/create-checkout-session', methods=['POST'])
@tenant_required
def create_checkout_session():
    """
    Create a Stripe checkout session for a payment
    """
    try:
        # Get the payment details from the request
        data = request.json
        amount = data.get('amount')
        currency = data.get('currency', 'usd')
        product_name = data.get('product_name', 'Invoice Payment')
        
        # Validate the required parameters
        if not amount:
            return jsonify({
                'success': False,
                'error': 'Amount is required'
            }), 400
        
        # Get the current domain
        domain = request.host
        
        # Create a checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'unit_amount': int(float(amount) * 100),  # Convert to cents
                    'product_data': {
                        'name': product_name,
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"https://{domain}{url_for('dashboard.index', payment_success=True)}",
            cancel_url=f"https://{domain}{url_for('dashboard.index', payment_cancelled=True)}",
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url
        })
    
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Stripe webhook events
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    # Verify the webhook signature
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # If no webhook secret is configured, parse the event data directly
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Handle successful payment
            # In a real implementation, we would update the database
            # and associate the payment with an invoice
            print(f"Payment succeeded for session {session.id}")
        
        return jsonify({'success': True})
    
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        # Invalid payload or signature
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@stripe_bp.route('/payments', methods=['GET'])
@tenant_required
def list_payments():
    """
    List payments for the connected Stripe account
    """
    # In a real implementation, we would retrieve the Stripe account details
    # from the database for the current tenant
    
    try:
        # Fetch payments from Stripe
        # This is a simplified example - in production we would use
        # proper pagination and filtering
        payments = stripe.PaymentIntent.list(limit=25)
        
        return jsonify({
            'success': True,
            'payments': payments.data
        })
    
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 400