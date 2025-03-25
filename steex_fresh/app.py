import os
from flask import Flask, render_template, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development-secret-key")

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/fresh-dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)