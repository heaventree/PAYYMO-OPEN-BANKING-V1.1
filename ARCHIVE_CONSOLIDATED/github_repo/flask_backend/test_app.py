import os
import logging
from flask import Flask, render_template, jsonify, request, session

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Set secret key for development
app.secret_key = "payymo_dev_secret_key"

# Mock data for testing
mock_stats = {
    'transactions': {'total': 125, 'total_amount': 12500.50, 'month': {'count': 42, 'amount': 4200.75}},
    'bank_connections': {'total': 3, 'active': 2},
    'matches': {'total': 85, 'confirmed': 70, 'pending': 15},
    'stripe_connections': {'total': 2, 'active': 2},
    'stripe_payments': {'total': 75, 'total_amount': 7500.25}
}

mock_transactions = [
    {
        'id': 1,
        'reference': 'TRX-001',
        'description': 'Monthly subscription payment',
        'amount': 99.99,
        'transaction_date': '2025-03-25',
        'bank_name': 'Demo Bank',
        'matches': []
    },
    {
        'id': 2,
        'reference': 'TRX-002',
        'description': 'Software license renewal',
        'amount': -199.50,
        'transaction_date': '2025-03-24',
        'bank_name': 'Test Bank',
        'matches': [{'id': 1}]
    },
    {
        'id': 3,
        'reference': 'TRX-003',
        'description': 'Customer payment',
        'amount': 350.00,
        'transaction_date': '2025-03-23',
        'bank_name': 'Demo Bank',
        'matches': []
    }
]

mock_bank_connections = [
    {
        'id': 1,
        'bank_name': 'Demo Bank',
        'status': 'active',
        'account_number': '****1234'
    },
    {
        'id': 2,
        'bank_name': 'Test Bank',
        'status': 'active',
        'account_number': '****5678'
    }
]

mock_stripe_connections = [
    {
        'id': 1,
        'account_name': 'Main Stripe Account',
        'email': 'billing@example.com',
        'status': 'active'
    }
]

mock_chart_data = {
    'amounts': [3500, 4200, 2800, 5100, 3800, 4500],
    'dates': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
}

class MockTransaction:
    def __init__(self, id, reference, description, amount, transaction_date, bank_name, matches):
        self.id = id
        self.reference = reference
        self.description = description
        self.amount = amount
        self.transaction_date = transaction_date
        self.bank_name = bank_name
        self.matches = matches
        
    @property
    def transaction_date(self):
        return self._transaction_date
        
    @transaction_date.setter
    def transaction_date(self, value):
        from datetime import datetime
        if isinstance(value, str):
            self._transaction_date = datetime.strptime(value, '%Y-%m-%d')
        else:
            self._transaction_date = value

# Mock transactions as objects
mock_transaction_objects = [
    MockTransaction(tx['id'], tx['reference'], tx['description'], tx['amount'], 
                   tx['transaction_date'], tx['bank_name'], tx['matches'])
    for tx in mock_transactions
]

class MockBankConnection:
    def __init__(self, id, bank_name, status, account_number):
        self.id = id
        self.bank_name = bank_name
        self.status = status
        self.account_number = account_number

# Mock bank connections as objects
mock_bank_connection_objects = [
    MockBankConnection(conn['id'], conn['bank_name'], conn['status'], conn['account_number'])
    for conn in mock_bank_connections
]

class MockStripeConnection:
    def __init__(self, id, account_name, email, status):
        self.id = id
        self.account_name = account_name
        self.email = email
        self.status = status

# Mock stripe connections as objects
mock_stripe_connection_objects = [
    MockStripeConnection(conn['id'], conn['account_name'], conn['email'], conn['status'])
    for conn in mock_stripe_connections
]

@app.route('/nobleui-dashboard')
def nobleui_dashboard():
    """NobleUI themed dashboard with mock data"""
    # Set session data for testing
    session['admin_logged_in'] = True
    session['tenant_id'] = 1
    session['authenticated'] = True
    
    return render_template(
        'dashboard/nobleui_dashboard.html',
        admin_session=True,
        tenant_id=1,
        stats=mock_stats,
        recent_transactions=mock_transaction_objects,
        bank_connections=mock_bank_connection_objects,
        stripe_connections=mock_stripe_connection_objects,
        chart_data=mock_chart_data
    )

@app.route('/api/ai-assistant', methods=['POST'])
def ai_assistant_api():
    """Mock API endpoint for AI Assistant interaction"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
            
        # Simple pattern matching for demo responses
        response_text = ""
        
        if "unmatched" in user_message.lower():
            response_text = f"You currently have 40 unmatched transactions. Would you like me to help you review them?"
        
        elif "invoicing status" in user_message.lower():
            response_text = f"Your invoicing status: 70 confirmed matches, 15 pending matches out of 85 total matches."
        
        elif "transaction patterns" in user_message.lower() or "analyze" in user_message.lower():
            response_text = f"Based on your recent transactions, your average transaction amount is £83.50. You've had 42 transactions this month. Would you like a more detailed analysis of your transaction patterns?"
        
        elif "optimization" in user_message.lower() or "tips" in user_message.lower():
            response_text = "Here are some optimization tips based on your financial data:\n\n"
            response_text += "1. You have 40 unmatched transactions. Consider reviewing these to improve your invoice matching.\n\n"
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 