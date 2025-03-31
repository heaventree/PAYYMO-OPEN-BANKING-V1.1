"""
Theme Previewer Blueprint
Allows viewing and previewing the HTML themes uploaded
Also serves static theme assets for use in the main application
"""

import os
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for, Response

# Create blueprint - we need both /themes for previews and /static/steex for application use
themes_bp = Blueprint('themes', __name__, url_prefix='/themes')

# Theme paths (using absolute paths for better reliability)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPROX_THEME_PATH = os.path.join(BASE_DIR, 'theme_preview/approx-v1.0/dist')
FLASK_ADMIN_THEME_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Admin/steex')
FLASK_ADMIN_TEMPLATES_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Admin/steex/templates')
FLASK_ADMIN_DOCS_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Documentation')

# Debug information
print(f"BASE_DIR: {BASE_DIR}")
print(f"APPROX_THEME_PATH: {APPROX_THEME_PATH}")
print(f"FLASK_ADMIN_THEME_PATH: {FLASK_ADMIN_THEME_PATH}")
print(f"FLASK_ADMIN_TEMPLATES_PATH: {FLASK_ADMIN_TEMPLATES_PATH}")
print(f"FLASK_ADMIN_DOCS_PATH: {FLASK_ADMIN_DOCS_PATH}")
print(f"Theme files exist? Approx: {os.path.exists(APPROX_THEME_PATH)}, Flask Admin: {os.path.exists(FLASK_ADMIN_THEME_PATH)}")

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
            .highlight {
                background-color: #fffacd;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 4px solid #ffd700;
            }
        </style>
    </head>
    <body>
        <h1>Admin Dashboard Theme Viewer</h1>
        <p class="description">Review and compare these admin dashboard themes for implementation in Payymo</p>
        
        <div class="highlight">
            <h2>Theme Browser</h2>
            <p>Use our new theme browser to explore and compare theme files with syntax highlighting:</p>
            <ul>
                <li><a href="/themes/browser" target="_blank">Open Theme Browser</a></li>
            </ul>
        </div>
        
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
    print(f"Serving approx file: {path}")
    print(f"Full path: {os.path.join(APPROX_THEME_PATH, path)}")
    print(f"File exists: {os.path.exists(os.path.join(APPROX_THEME_PATH, path))}")
    
    if os.path.exists(os.path.join(APPROX_THEME_PATH, path)):
        return send_from_directory(APPROX_THEME_PATH, path)
    
    return f"File not found: {path}", 404

@themes_bp.route('/flask-admin/dashboard')
def flask_admin_dashboard():
    """Serve Flask Admin dashboard page"""
    dashboard_path = os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards', 'index.html')
    print(f"Serving flask admin dashboard from: {dashboard_path}")
    print(f"File exists: {os.path.exists(dashboard_path)}")
    
    if os.path.exists(dashboard_path):
        return send_from_directory(os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards'), 'index.html')
    
    return "Dashboard file not found", 404

@themes_bp.route('/flask-admin/docs')
def flask_admin_documentation():
    """Serve Flask Admin documentation"""
    docs_path = os.path.join(FLASK_ADMIN_DOCS_PATH, 'index.html')
    print(f"Serving flask admin docs from: {docs_path}")
    print(f"File exists: {os.path.exists(docs_path)}")
    
    if os.path.exists(docs_path):
        return send_from_directory(FLASK_ADMIN_DOCS_PATH, 'index.html')
    
    return "Documentation not found", 404

@themes_bp.route('/flask-admin/admin/<path:path>')
def flask_admin_admin(path):
    """Serve admin pages from the Flask Admin theme"""
    print(f"Looking for admin page: {path}")
    
    # Try to find the appropriate template
    for root, dirs, files in os.walk(FLASK_ADMIN_TEMPLATES_PATH):
        for file in files:
            if file == path + '.html' or file == path:
                relative_path = os.path.relpath(os.path.join(root, file), FLASK_ADMIN_TEMPLATES_PATH)
                print(f"Found file at: {relative_path}")
                return send_from_directory(FLASK_ADMIN_TEMPLATES_PATH, relative_path)
    
    print(f"Admin page not found: {path}")
    # Default to dashboard if page not found
    dashboard_path = os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards', 'index.html')
    if os.path.exists(dashboard_path):
        return send_from_directory(os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards'), 'index.html')
    
    return f"Admin page not found: {path}", 404

@themes_bp.route('/flask-admin/<path:path>')
def serve_flask_admin(path):
    """Serve static files from the Flask Admin theme"""
    print(f"Looking for flask admin file: {path}")
    
    # Check if it's a static file (CSS, JS, images)
    if path.startswith('static/'):
        full_path = os.path.join(FLASK_ADMIN_THEME_PATH, path)
        print(f"Checking static path: {full_path}")
        if os.path.exists(full_path):
            return send_from_directory(FLASK_ADMIN_THEME_PATH, path)
    
    # Try to find the file in Documentation
    docs_path = os.path.join(FLASK_ADMIN_DOCS_PATH, path)
    print(f"Checking docs path: {docs_path}")
    if os.path.exists(docs_path):
        return send_from_directory(FLASK_ADMIN_DOCS_PATH, path)
    
    # Try to find the file in Admin
    admin_path = os.path.join(FLASK_ADMIN_THEME_PATH, path)
    print(f"Checking admin path: {admin_path}")
    if os.path.exists(admin_path):
        return send_from_directory(FLASK_ADMIN_THEME_PATH, path)
    
    print(f"File not found: {path}")
    return f"File not found: {path}", 404

@themes_bp.route('/browser')
def theme_browser():
    """Display a browser for theme files"""
    # Get HTML files from Approx theme
    approx_files = []
    for file in os.listdir(APPROX_THEME_PATH):
        if file.endswith('.html'):
            approx_files.append(file)
    approx_files.sort()
    
    # Get HTML files from Flask Admin theme templates
    flask_admin_files = []
    for root, dirs, files in os.walk(FLASK_ADMIN_TEMPLATES_PATH):
        for file in files:
            if file.endswith('.html'):
                # Get relative path from templates directory
                rel_path = os.path.relpath(os.path.join(root, file), FLASK_ADMIN_TEMPLATES_PATH)
                flask_admin_files.append(rel_path)
    flask_admin_files.sort()
    
    return render_template('theme_browser.html', 
                           approx_files=approx_files,
                           flask_admin_files=flask_admin_files)

@themes_bp.route('/approx-content/<path:filename>')
def approx_content(filename):
    """Return the content of an Approx theme file"""
    file_path = os.path.join(APPROX_THEME_PATH, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    return "File not found", 404

@themes_bp.route('/flask-admin-content/<path:filename>')
def flask_admin_content(filename):
    """Return the content of a Flask Admin theme file"""
    file_path = os.path.join(FLASK_ADMIN_TEMPLATES_PATH, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    return "File not found", 404

@themes_bp.route('/steex/<path:path>')
def steex_assets(path):
    """Serve static assets from the Steex admin theme for use in the main app"""
    # First check if file exists in the main steex directory
    asset_path = os.path.join(FLASK_ADMIN_THEME_PATH, path)
    if os.path.exists(asset_path):
        return send_from_directory(FLASK_ADMIN_THEME_PATH, path)
    
    # Check if it's in assets folder
    if path.startswith('assets/'):
        relative_path = path[7:]  # Remove 'assets/' prefix
        asset_path = os.path.join(FLASK_ADMIN_THEME_PATH, 'assets', relative_path)
        if os.path.exists(asset_path):
            return send_from_directory(os.path.join(FLASK_ADMIN_THEME_PATH, 'assets'), relative_path)
    
    # Check if it's in the static folder
    if path.startswith('static/'):
        relative_path = path[7:]  # Remove 'static/' prefix
        asset_path = os.path.join(FLASK_ADMIN_THEME_PATH, 'static', relative_path)
        if os.path.exists(asset_path):
            return send_from_directory(os.path.join(FLASK_ADMIN_THEME_PATH, 'static'), relative_path)
    
    # If all else fails, check if it's directly in the assets folder
    asset_path = os.path.join(FLASK_ADMIN_THEME_PATH, 'assets', path)
    if os.path.exists(asset_path):
        return send_from_directory(os.path.join(FLASK_ADMIN_THEME_PATH, 'assets'), path)
    
    return f"Steex asset not found: {path}", 404