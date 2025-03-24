#!/usr/bin/env python3
from flask import Flask, render_template, send_from_directory, redirect, url_for
import os

app = Flask(__name__, static_folder=None)

# Theme paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPROX_THEME_PATH = os.path.join(BASE_DIR, 'theme_preview/approx-v1.0/dist')
FLASK_ADMIN_THEME_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Admin/steex')
FLASK_ADMIN_TEMPLATES_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Admin/steex/templates')
FLASK_ADMIN_DOCS_PATH = os.path.join(BASE_DIR, 'flask_admin_theme/Documentation')

print(f"BASE_DIR: {BASE_DIR}")
print(f"APPROX_THEME_PATH: {APPROX_THEME_PATH}")
print(f"FLASK_ADMIN_THEME_PATH: {FLASK_ADMIN_THEME_PATH}")
print(f"FLASK_ADMIN_TEMPLATES_PATH: {FLASK_ADMIN_TEMPLATES_PATH}")
print(f"FLASK_ADMIN_DOCS_PATH: {FLASK_ADMIN_DOCS_PATH}")
print(f"Theme files exist? Approx: {os.path.exists(APPROX_THEME_PATH)}, Flask Admin: {os.path.exists(FLASK_ADMIN_THEME_PATH)}")

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
                <li><a href="/approx/index.html">Dashboard</a></li>
                <li><a href="/approx/analytics-customers.html">Analytics - Customers</a></li>
                <li><a href="/approx/analytics-reports.html">Analytics - Reports</a></li>
                <li><a href="/approx/apps-invoice.html">Invoice</a></li>
                <li><a href="/approx-list">View All Approx Pages</a></li>
            </ul>
        </div>
        
        <div class="theme-section">
            <h2>Flask Admin Theme</h2>
            <p>Flask-specific admin dashboard template with integrated Python framework support</p>
            <ul>
                <li><a href="/flask-admin/dashboard">Dashboard</a></li>
                <li><a href="/flask-admin/docs">Documentation</a></li>
                <li><a href="/flask-admin/admin/calendar">Calendar</a></li>
                <li><a href="/flask-admin-list">View All Flask Admin Pages</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/approx-list')
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
        <a href="/" class="back-link">← Back to Theme Selector</a>
        <h1>Approx Theme Pages</h1>
        <ul>
            {''.join([f'<li><a href="/approx/{file}">{file}</a></li>' for file in files])}
        </ul>
    </body>
    </html>
    """

@app.route('/flask-admin-list')
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
        <a href="/" class="back-link">← Back to Theme Selector</a>
        <h1>Flask Admin Theme Pages</h1>
        
        <div class="section">
            <h2>Main Pages</h2>
            <ul>
                <li><a href="/flask-admin/dashboard">Dashboard</a></li>
                <li><a href="/flask-admin/docs">Documentation</a></li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Admin Pages</h2>
            <ul>
                <li><a href="/flask-admin/admin/dashboard">Admin Dashboard</a></li>
                <li><a href="/flask-admin/admin/calendar">Calendar</a></li>
                <li><a href="/flask-admin/admin/chat">Chat</a></li>
                <li><a href="/flask-admin/admin/invoice-list">Invoice List</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/view/<theme>/<path:page>')
def theme_viewer(theme, page):
    """Render the theme viewer with embedded theme page"""
    if theme == 'approx':
        iframe_src = f"/approx-direct/{page}"
        theme_name = "Approx HTML Admin"
    elif theme == 'flask-admin':
        iframe_src = f"/flask-admin-direct/{page}"
        theme_name = "Flask Admin"
    else:
        return "Invalid theme", 404
    
    return render_template('flask_backend/templates/theme_viewer.html', 
                          theme_name=theme_name,
                          page_title=page,
                          iframe_src=iframe_src,
                          back_url="/")

@app.route('/approx/<path:path>')
def serve_approx(path):
    """Serve files from the Approx theme through the viewer"""
    return redirect(url_for('theme_viewer', theme='approx', page=path))

@app.route('/approx-direct/<path:path>')
def serve_approx_direct(path):
    """Directly serve files from the Approx theme"""
    print(f"Serving approx file: {path}")
    print(f"Full path: {os.path.join(APPROX_THEME_PATH, path)}")
    print(f"File exists: {os.path.exists(os.path.join(APPROX_THEME_PATH, path))}")
    
    return send_from_directory(APPROX_THEME_PATH, path)

@app.route('/flask-admin/dashboard')
def flask_admin_dashboard():
    """Serve Flask Admin dashboard page through the viewer"""
    return redirect(url_for('theme_viewer', theme='flask-admin', page='dashboard'))

@app.route('/flask-admin-direct/dashboard')
def flask_admin_dashboard_direct():
    """Directly serve Flask Admin dashboard page"""
    dashboard_path = os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards', 'index.html')
    print(f"Serving flask admin dashboard from: {dashboard_path}")
    print(f"File exists: {os.path.exists(dashboard_path)}")
    
    return send_from_directory(os.path.join(FLASK_ADMIN_TEMPLATES_PATH, 'dashboards'), 'index.html')

@app.route('/flask-admin/docs')
def flask_admin_documentation():
    """Serve Flask Admin documentation through the viewer"""
    return redirect(url_for('theme_viewer', theme='flask-admin', page='docs'))

@app.route('/flask-admin-direct/docs')
def flask_admin_documentation_direct():
    """Directly serve Flask Admin documentation"""
    docs_path = os.path.join(FLASK_ADMIN_DOCS_PATH, 'index.html')
    print(f"Serving flask admin docs from: {docs_path}")
    print(f"File exists: {os.path.exists(docs_path)}")
    
    return send_from_directory(FLASK_ADMIN_DOCS_PATH, 'index.html')

@app.route('/flask-admin/admin/<path:path>')
def flask_admin_admin(path):
    """Serve admin pages from the Flask Admin theme through the viewer"""
    return redirect(url_for('theme_viewer', theme='flask-admin', page=f"admin/{path}"))

@app.route('/flask-admin-direct/admin/<path:path>')
def flask_admin_admin_direct(path):
    """Directly serve admin pages from the Flask Admin theme"""
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

@app.route('/flask-admin-direct/<path:path>')
def serve_flask_admin_direct(path):
    """Directly serve static files from the Flask Admin theme"""
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)