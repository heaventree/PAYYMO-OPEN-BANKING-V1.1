#!/usr/bin/env python3
"""
Theme Explorer - A simple file server for exploring the HTML theme files

This standalone application serves static files from the theme folders
and provides a simple interface for browsing and comparing themes.
"""
from flask import Flask, send_from_directory, render_template_string, redirect
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('theme_explorer')

app = Flask(__name__)

# Theme paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPROX_THEME_PATH = os.path.join(BASE_DIR, 'theme_preview', 'approx-v1.0', 'dist')
FLASK_ADMIN_THEME_PATH = os.path.join(BASE_DIR, 'flask_admin_theme', 'Admin', 'steex')
FLASK_ADMIN_STATIC_PATH = os.path.join(FLASK_ADMIN_THEME_PATH, 'static')
FLASK_ADMIN_TEMPLATES_PATH = os.path.join(FLASK_ADMIN_THEME_PATH, 'templates')

# Check if paths exist and log results
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"APPROX_THEME_PATH exists: {os.path.exists(APPROX_THEME_PATH)}")
logger.info(f"FLASK_ADMIN_THEME_PATH exists: {os.path.exists(FLASK_ADMIN_THEME_PATH)}")
logger.info(f"FLASK_ADMIN_TEMPLATES_PATH exists: {os.path.exists(FLASK_ADMIN_TEMPLATES_PATH)}")

# Main index with links to themes
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theme Explorer</title>
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
    <h1>Theme Explorer</h1>
    <p class="description">Browse and compare the HTML admin dashboard themes</p>
    
    <div class="theme-section">
        <h2>Approx HTML Admin Dashboard</h2>
        <p>Full featured admin dashboard template with analytics, reporting, and invoice components</p>
        <ul>
            <li><a href="/approx/index.html" target="_blank">Dashboard</a></li>
            <li><a href="/approx/analytics-customers.html" target="_blank">Analytics - Customers</a></li>
            <li><a href="/approx/analytics-reports.html" target="_blank">Analytics - Reports</a></li>
            <li><a href="/approx/apps-invoice.html" target="_blank">Invoice</a></li>
            <li><a href="/approx-list" target="_blank">Browse All Pages</a></li>
        </ul>
    </div>
    
    <div class="theme-section">
        <h2>Flask Admin Theme Files</h2>
        <p>Browse Flask Admin theme files directly</p>
        <ul>
            <li><a href="/flask-admin-templates" target="_blank">Templates Directory</a></li>
            <li><a href="/flask-admin-static" target="_blank">Static Assets</a></li>
        </ul>
    </div>
</body>
</html>
"""

# File browser HTML template
FILE_BROWSER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .path-info {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-family: monospace;
            word-break: break-all;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .file-icon, .folder-icon {
            margin-right: 8px;
        }
        .file-icon {
            color: #607d8b;
        }
        .folder-icon {
            color: #ffc107;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            padding: 8px 16px;
            background-color: #f0f0f0;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
        }
        .back-link:hover {
            background-color: #e0e0e0;
        }
        .file-size {
            color: #666;
            font-size: 0.9em;
        }
        .file-type {
            color: #888;
            font-size: 0.9em;
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
    <a href="{{ back_url }}" class="back-link">← Back</a>
    <h1>{{ title }}</h1>
    <div class="path-info">{{ current_path }}</div>
    
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Size</th>
            </tr>
        </thead>
        <tbody>
            {% if parent_dir %}
            <tr>
                <td><a href="{{ parent_url }}"><span class="folder-icon">📁</span> ..</a></td>
                <td>Directory</td>
                <td></td>
            </tr>
            {% endif %}
            
            {% for item in items %}
            <tr>
                <td>
                    {% if item.is_dir %}
                    <a href="{{ item.url }}"><span class="folder-icon">📁</span> {{ item.name }}</a>
                    {% else %}
                    <a href="{{ item.url }}" target="_blank"><span class="file-icon">📄</span> {{ item.name }}</a>
                    {% endif %}
                </td>
                <td class="file-type">{{ item.type }}</td>
                <td class="file-size">{{ item.size }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with links to both themes"""
    return render_template_string(INDEX_HTML)

@app.route('/approx/<path:path>')
def serve_approx(path):
    """Serve files from the Approx theme"""
    logger.info(f"Serving Approx file: {path}")
    return send_from_directory(APPROX_THEME_PATH, path)

@app.route('/approx-list')
def approx_file_list():
    """Browse Approx theme files"""
    return browse_directory(APPROX_THEME_PATH, 'Approx Theme Files', '/approx', '/')

@app.route('/flask-admin-templates')
def flask_admin_templates_root():
    """Browse Flask Admin template files"""
    return browse_directory(FLASK_ADMIN_TEMPLATES_PATH, 'Flask Admin Templates', '/flask-admin-templates', '/')

@app.route('/flask-admin-static')
def flask_admin_static_root():
    """Browse Flask Admin static files"""
    return browse_directory(FLASK_ADMIN_STATIC_PATH, 'Flask Admin Static Assets', '/flask-admin-static', '/')

@app.route('/flask-admin-templates/<path:path>')
def browse_flask_admin_templates(path):
    """Browse Flask Admin template subdirectories"""
    full_path = os.path.join(FLASK_ADMIN_TEMPLATES_PATH, path)
    if os.path.isdir(full_path):
        # Directory - browse contents
        parent_path = os.path.dirname(path)
        parent_url = f'/flask-admin-templates/{parent_path}' if parent_path else '/flask-admin-templates'
        return browse_directory(full_path, f'Templates: /{path}', '/flask-admin-templates', parent_url)
    else:
        # File - serve it
        return send_from_directory(FLASK_ADMIN_TEMPLATES_PATH, path)

@app.route('/flask-admin-static/<path:path>')
def serve_flask_admin_static(path):
    """Serve Flask Admin static files"""
    full_path = os.path.join(FLASK_ADMIN_STATIC_PATH, path)
    if os.path.isdir(full_path):
        # Directory - browse contents
        parent_path = os.path.dirname(path)
        parent_url = f'/flask-admin-static/{parent_path}' if parent_path else '/flask-admin-static'
        return browse_directory(full_path, f'Static Assets: /{path}', '/flask-admin-static', parent_url)
    else:
        # File - serve it
        return send_from_directory(FLASK_ADMIN_STATIC_PATH, path)

def get_file_size(file_path):
    """Get human-readable file size"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

def get_file_type(file_path):
    """Get file type based on extension"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == '.html':
        return 'HTML Document'
    elif ext in ['.js', '.jsx']:
        return 'JavaScript'
    elif ext in ['.css', '.scss', '.sass']:
        return 'Stylesheet'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
        return 'Image'
    elif ext in ['.ttf', '.woff', '.woff2', '.eot']:
        return 'Font'
    elif ext in ['.json', '.xml']:
        return 'Data'
    elif ext == '.md':
        return 'Markdown'
    elif ext == '.py':
        return 'Python'
    else:
        return ext[1:].upper() if ext else 'Unknown'

def browse_directory(dir_path, title, base_url, back_url):
    """Generate HTML to browse a directory"""
    if not os.path.exists(dir_path):
        return f"Directory not found: {dir_path}", 404
    
    # Get items in directory
    items = []
    for name in sorted(os.listdir(dir_path)):
        if name.startswith('.'):
            continue  # Skip hidden files
            
        full_path = os.path.join(dir_path, name)
        is_dir = os.path.isdir(full_path)
        
        item = {
            'name': name,
            'is_dir': is_dir,
            'url': f"{base_url}/{name}" if is_dir or base_url == '/approx' else f"{base_url}/{name}",
            'type': 'Directory' if is_dir else get_file_type(full_path),
            'size': '' if is_dir else get_file_size(full_path)
        }
        items.append(item)
    
    # Sort directories first, then files
    items.sort(key=lambda x: (0 if x['is_dir'] else 1, x['name']))
    
    return render_template_string(
        FILE_BROWSER_TEMPLATE,
        title=title,
        current_path=dir_path,
        items=items,
        back_url=back_url,
        parent_dir=True if back_url != '/' else False,
        parent_url=back_url
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)