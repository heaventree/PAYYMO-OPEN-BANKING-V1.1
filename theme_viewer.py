import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    """Landing page with links to both themes"""
    return """
    <html>
    <head>
        <title>Theme Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            .theme-section {
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            ul {
                padding-left: 20px;
            }
            li {
                margin-bottom: 8px;
            }
            a {
                color: #0066cc;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Theme Viewer</h1>
        
        <div class="theme-section">
            <h2>Approx HTML Admin Dashboard</h2>
            <p>Full featured admin dashboard template</p>
            <ul>
                <li><a href="/approx/index.html" target="_blank">Dashboard</a></li>
                <li><a href="/approx/analytics-customers.html" target="_blank">Analytics - Customers</a></li>
                <li><a href="/approx/analytics-reports.html" target="_blank">Analytics - Reports</a></li>
                <li><a href="/approx/apps-invoice.html" target="_blank">Invoice</a></li>
                <li><a href="/approx/" target="_blank">All Approx Pages</a></li>
            </ul>
        </div>
        
        <div class="theme-section">
            <h2>Flask Admin Theme</h2>
            <p>Flask-specific admin dashboard template</p>
            <ul>
                <li><a href="/flask-admin/index" target="_blank">Dashboard</a></li>
                <li><a href="/flask-admin/documentation" target="_blank">Documentation</a></li>
                <li><a href="/flask-admin/" target="_blank">All Flask Admin Pages</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/approx/')
def approx_index():
    """List all pages in the Approx theme"""
    files = []
    base_dir = 'theme_preview/approx-v1.0/dist'
    for file in os.listdir(base_dir):
        if file.endswith('.html'):
            files.append(file)
    files.sort()
    
    return f"""
    <html>
    <head>
        <title>Approx Theme Pages</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 8px; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .back-link {{ margin-bottom: 20px; display: block; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Theme Selector</a>
        <h1>Approx Theme Pages</h1>
        <ul>
            {''.join([f'<li><a href="/approx/{file}" target="_blank">{file}</a></li>' for file in files])}
        </ul>
    </body>
    </html>
    """

@app.route('/flask-admin/')
def flask_admin_index():
    """List key pages in the Flask Admin theme"""
    return f"""
    <html>
    <head>
        <title>Flask Admin Theme Pages</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 8px; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .back-link {{ margin-bottom: 20px; display: block; }}
            .section {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Theme Selector</a>
        <h1>Flask Admin Theme Pages</h1>
        
        <div class="section">
            <h2>Main Pages</h2>
            <ul>
                <li><a href="/flask-admin/index" target="_blank">Dashboard</a></li>
                <li><a href="/flask-admin/documentation" target="_blank">Documentation</a></li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Admin Pages</h2>
            <ul>
                <li><a href="/flask-admin/admin/dashboard" target="_blank">Admin Dashboard</a></li>
                <li><a href="/flask-admin/admin/calendar" target="_blank">Calendar</a></li>
                <li><a href="/flask-admin/admin/chat" target="_blank">Chat</a></li>
                <li><a href="/flask-admin/admin/invoice-list" target="_blank">Invoice List</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/approx/<path:path>')
def serve_approx(path):
    """Serve files from the Approx theme"""
    if path.endswith('.html'):
        return send_from_directory('theme_preview/approx-v1.0/dist', path)
    
    # For assets like CSS, JS, images
    return send_from_directory('theme_preview/approx-v1.0/dist', path)

@app.route('/flask-admin/index')
def flask_admin_dashboard():
    """Serve Flask Admin dashboard page"""
    return send_from_directory('flask_admin_theme/Admin/steex/templates/dashboards', 'index.html')

@app.route('/flask-admin/documentation')
def flask_admin_documentation():
    """Serve Flask Admin documentation"""
    return send_from_directory('flask_admin_theme/Documentation', 'index.html')

@app.route('/flask-admin/admin/<path:path>')
def flask_admin_admin(path):
    """Serve admin pages from the Flask Admin theme"""
    # Try to find the appropriate template
    for root, dirs, files in os.walk('flask_admin_theme/Admin/steex/templates'):
        for file in files:
            if file == path + '.html' or file == path:
                relative_path = os.path.join(root, file).replace('flask_admin_theme/Admin/steex/templates/', '')
                return send_from_directory('flask_admin_theme/Admin/steex/templates', relative_path)
    
    # Default to dashboard if page not found
    return send_from_directory('flask_admin_theme/Admin/steex/templates/dashboards', 'index.html')

@app.route('/flask-admin/<path:path>')
def serve_flask_admin(path):
    """Serve static files from the Flask Admin theme"""
    # Check if it's a static file (CSS, JS, images)
    if path.startswith('static/'):
        return send_from_directory('flask_admin_theme/Admin/steex', path)
        
    # Try to find the file in Documentation
    if os.path.exists(os.path.join('flask_admin_theme/Documentation', path)):
        return send_from_directory('flask_admin_theme/Documentation', path)
        
    # Try to find the file in Admin
    if os.path.exists(os.path.join('flask_admin_theme/Admin/steex', path)):
        return send_from_directory('flask_admin_theme/Admin/steex', path)
        
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)