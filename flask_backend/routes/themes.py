"""
Theme Previewer Blueprint
Allows viewing and previewing the HTML themes uploaded
"""

import os
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for

# Create blueprint
themes_bp = Blueprint('themes', __name__, url_prefix='/themes')

# Theme paths
APPROX_THEME_PATH = 'theme_preview/approx-v1.0/dist'
FLASK_ADMIN_THEME_PATH = 'flask_admin_theme/Admin/steex'
FLASK_ADMIN_TEMPLATES_PATH = 'flask_admin_theme/Admin/steex/templates'
FLASK_ADMIN_DOCS_PATH = 'flask_admin_theme/Documentation'

@themes_bp.route('/')
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
                color: #333;
            }
            h1, h2 {
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            .theme-section {
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
            .description {
                color: #666;
                font-style: italic;
                margin-bottom: 15px;
            }
        </style>
    </head>
    <body>
        <h1>Admin Dashboard Theme Viewer</h1>
        <p class="description">Review and compare these admin dashboard themes for implementation in Payymo</p>
        
        <div class="theme-section">
            <h2>Approx HTML Admin Dashboard</h2>
            <p>Full featured admin dashboard template with analytics, reporting, and invoice components</p>
            <ul>
                <li><a href="/themes/approx/index.html" target="_blank">Dashboard</a></li>
                <li><a href="/themes/approx/analytics-customers.html" target="_blank">Analytics - Customers</a></li>
                <li><a href="/themes/approx/analytics-reports.html" target="_blank">Analytics - Reports</a></li>
                <li><a href="/themes/approx/apps-invoice.html" target="_blank">Invoice</a></li>
                <li><a href="/themes/approx-list" target="_blank">View All Approx Pages</a></li>
            </ul>
        </div>
        
        <div class="theme-section">
            <h2>Flask Admin Theme</h2>
            <p>Flask-specific admin dashboard template with integrated Python framework support</p>
            <ul>
                <li><a href="/themes/flask-admin/dashboard" target="_blank">Dashboard</a></li>
                <li><a href="/themes/flask-admin/docs" target="_blank">Documentation</a></li>
                <li><a href="/themes/flask-admin/admin/calendar" target="_blank">Calendar</a></li>
                <li><a href="/themes/flask-admin-list" target="_blank">View All Flask Admin Pages</a></li>
            </ul>
        </div>
        
        <div class="theme-section">
            <h2>Return to Main App</h2>
            <p>Go back to the main Payymo application</p>
            <ul>
                <li><a href="/" target="_blank">Payymo Dashboard</a></li>
                <li><a href="/dashboard-redesign" target="_blank">Payymo Dashboard Redesign</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@themes_bp.route('/approx-list')
def approx_index():
    """List all pages in the Approx theme"""
    files = []
    base_dir = APPROX_THEME_PATH
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
        <a href="/themes" class="back-link">← Back to Theme Selector</a>
        <h1>Approx Theme Pages</h1>
        <ul>
            {''.join([f'<li><a href="/themes/approx/{file}" target="_blank">{file}</a></li>' for file in files])}
        </ul>
    </body>
    </html>
    """

@themes_bp.route('/flask-admin-list')
def flask_admin_index():
    """List key pages in the Flask Admin theme"""
    return f"""
    <html>
    <head>
        <title>Flask Admin Theme Pages</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1, h2 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 8px; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .back-link {{ margin-bottom: 20px; display: block; }}
            .section {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <a href="/themes" class="back-link">← Back to Theme Selector</a>
        <h1>Flask Admin Theme Pages</h1>
        
        <div class="section">
            <h2>Main Pages</h2>
            <ul>
                <li><a href="/themes/flask-admin/dashboard" target="_blank">Dashboard</a></li>
                <li><a href="/themes/flask-admin/docs" target="_blank">Documentation</a></li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Admin Pages</h2>
            <ul>
                <li><a href="/themes/flask-admin/admin/dashboard" target="_blank">Admin Dashboard</a></li>
                <li><a href="/themes/flask-admin/admin/calendar" target="_blank">Calendar</a></li>
                <li><a href="/themes/flask-admin/admin/chat" target="_blank">Chat</a></li>
                <li><a href="/themes/flask-admin/admin/invoice-list" target="_blank">Invoice List</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@themes_bp.route('/approx/<path:path>')
def serve_approx(path):
    """Serve files from the Approx theme"""
    return send_from_directory(APPROX_THEME_PATH, path)

@themes_bp.route('/flask-admin/dashboard')
def flask_admin_dashboard():
    """Serve Flask Admin dashboard page"""
    return send_from_directory(os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards'), 'index.html')

@themes_bp.route('/flask-admin/docs')
def flask_admin_documentation():
    """Serve Flask Admin documentation"""
    return send_from_directory(FLASK_ADMIN_DOCS_PATH, 'index.html')

@themes_bp.route('/flask-admin/admin/<path:path>')
def flask_admin_admin(path):
    """Serve admin pages from the Flask Admin theme"""
    # Try to find the appropriate template
    for root, dirs, files in os.walk(FLASK_ADMIN_TEMPLATES_PATH):
        for file in files:
            if file == path + '.html' or file == path:
                relative_path = os.path.join(root, file).replace(FLASK_ADMIN_TEMPLATES_PATH + '/', '')
                return send_from_directory(FLASK_ADMIN_TEMPLATES_PATH, relative_path)
    
    # Default to dashboard if page not found
    return send_from_directory(os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards'), 'index.html')

@themes_bp.route('/flask-admin/<path:path>')
def serve_flask_admin(path):
    """Serve static files from the Flask Admin theme"""
    # Check if it's a static file (CSS, JS, images)
    if path.startswith('static/'):
        return send_from_directory(FLASK_ADMIN_THEME_PATH, path)
        
    # Try to find the file in Documentation
    if os.path.exists(os.path.join(FLASK_ADMIN_DOCS_PATH, path)):
        return send_from_directory(FLASK_ADMIN_DOCS_PATH, path)
        
    # Try to find the file in Admin
    if os.path.exists(os.path.join(FLASK_ADMIN_THEME_PATH, path)):
        return send_from_directory(FLASK_ADMIN_THEME_PATH, path)
        
    return "File not found", 404