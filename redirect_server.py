#!/usr/bin/env python
"""
Redirect Server
A simple server that redirects root requests to the NobleUI dashboard.
Run this in addition to the main Flask app.
"""

from flask import Flask, send_file, redirect

app = Flask(__name__)

@app.route('/')
def index():
    """Redirect to the NobleUI dashboard"""
    return send_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)