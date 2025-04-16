#!/usr/bin/env python
"""
Dashboard Switcher
A minimal Flask application that intercepts root requests and redirects to the NobleUI dashboard.
"""

import os
from flask import Flask, redirect

# Create a minimal Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Redirect to the NobleUI dashboard"""
    return redirect('/nobleui-dashboard')

# Only run this as a standalone server if explicitly executed
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)