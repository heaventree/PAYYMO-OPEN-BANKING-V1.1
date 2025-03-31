# Payymo Project Management Guide

## Table of Contents
1. [Development Standards](#development-standards)
2. [Backup Standards](#backup-standards)
3. [CSS Management](#css-management)
4. [Error Recovery](#error-recovery)
5. [User Interface Standards](#user-interface-standards)

## Development Standards

### Code Organization
- Follow the established project structure
- Use proper namespacing and module patterns
- Follow the Flask template inheritance pattern
- Keep business logic in services, not routes
- Use typed interfaces where appropriate

### Coding Standards
- Follow PEP 8 for Python code
- Use ES6+ for JavaScript
- Document all functions with docstrings
- Implement proper error handling
- Follow SQLAlchemy patterns for database operations

### Testing Requirements
- Write unit tests for critical functionality
- Test all API endpoints
- Verify database operations
- Test OAuth flows with mock services
- Validate UI rendering

## Backup Standards

### Pre-Modification Backup Process
**MANDATORY**: Before making any potentially disruptive changes to the application, create backups following this process:

```bash
# Create timestamped backup directory
mkdir -p ./backups/$(date +%Y%m%d_%H%M%S)

# Copy all files that will be modified
cp -r ./flask_backend/templates ./backups/$(ls -tr ./backups/ | tail -1)/
cp -r ./flask_backend/static ./backups/$(ls -tr ./backups/ | tail -1)/
# Add any additional directories that will be affected

# Document what changes are being made
echo "Backup created before: [DESCRIBE CHANGES]" > ./backups/$(ls -tr ./backups/ | tail -1)/README.md
```

### Automated Backup System
The project includes an automated backup system with these scripts:
- `backup_chat.py` - Saves conversation history and code snippets
- `save_approved.py` - Creates approved revision snapshots
- `rollback_to_approved.py` - Restores to previous approved states

Use this system for regular backups:
```python
# Create a snapshot of the current state
python save_approved.py "Feature Name" "Description of the current state"

# In case of issues, rollback to a previous state
python rollback_to_approved.py
```

### GitHub-Ready Backups
Important milestones should be saved to the GitHub-ready backups folder:
```bash
# Create a clean backup suitable for GitHub
python backup_chat.py --github-backup
```

## CSS Management

### CSS File Organization
**IMPORTANT**: The project must maintain a single source of truth for CSS styles.

1. Use **ONLY ONE** CSS file per theme:
   - `style.css` - Main CSS file for light theme
   - Additional theme files should be clearly named (e.g., `dark-theme.css`)

2. Include CSS files in the main layout template:
```html
<!-- In layout.html -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
{% if dark_mode %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/dark-theme.css') }}">
{% endif %}
```

3. Do not include CSS files in individual page templates:
   - Use the `{% block styles %}{% endblock %}` block in layout.html
   - Page-specific styles should be included in this block

4. Use CSS custom properties for theme variables:
```css
:root {
  --color-primary: #4CAF50;
  --color-secondary: #E91E63;
  /* Other theme variables */
}
```

### Style Modification Process
When modifying styles:
1. First create a backup of all CSS files
2. Make changes to a single file at a time
3. Test changes before moving to the next file
4. Remove unused/duplicate CSS files
5. Document the purpose of each CSS rule

## Error Recovery

### Common Issues and Solutions
1. Missing Templates:
   - Check backup folders for previous versions
   - Restore from GitHub-ready backups if needed
   
2. Database Connection Issues:
   - Verify DATABASE_URL environment variable
   - Check PostgreSQL service status
   
3. OAuth Integration Problems:
   - Validate client credentials
   - Check for API version mismatches
   - Review error logs for specific issues

### Logging and Debugging
Use the built-in logging system:
```python
import logging
logging.debug("Detailed information")
logging.info("Confirmation that things are working")
logging.warning("Something unexpected happened")
logging.error("Something failed")
```

## User Interface Standards

### WHMCS Style Compatibility
- Use light theme consistent with WHMCS admin panel
- Top navigation layout (not sidebar)
- Use Bootstrap 5 components
- Follow standard WHMCS color scheme

### UI Components
- Cards for content grouping
- Tables for data display
- Modal dialogs for wizards
- Forms with proper validation
- Toast notifications for alerts

### Responsive Design
- Desktop-first approach (matches WHMCS)
- Support tablet and mobile views
- Use Bootstrap's grid system
- Test all breakpoints

### JavaScript Standards
- Use vanilla JS or minimal jQuery
- Implement proper event delegation
- Separate concerns with module pattern
- Add proper error handling
- Document complex functionality