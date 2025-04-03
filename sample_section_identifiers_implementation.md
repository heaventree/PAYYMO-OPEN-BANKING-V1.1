# Sample Section Identifiers Implementation

Here is a complete sample implementation that can be directly applied to other projects.

## 1. HTML Integration (in your base template)

```html
<!-- In the <head> section -->
<link rel="stylesheet" href="/static/css/section-identifiers.css">

<!-- In your navigation bar or toolbar area -->
<div class="form-check form-switch me-3">
    <input class="form-check-input" type="checkbox" id="sectionIdentifiersToggle">
    <label class="form-check-label small" for="sectionIdentifiersToggle">
        <i class="icon-layout-grid me-1"></i>
        Section IDs
    </label>
</div>

<!-- At the end of your <body> section -->
<script src="/static/js/section-identifiers.js"></script>
```

## 2. CSS Implementation (`section-identifiers.css`)

```css
/* 
 * Section Identifiers System
 * Simple sequential section numbering system for development and support
 */

/* Core section identifier styles */
.section-identifier {
    display: none;
    position: absolute;
    top: 0;
    left: 0;
    font-size: 12px;
    font-weight: bold;
    padding: 2px 6px;
    background-color: rgba(0, 0, 255, 0.7);
    color: white;
    border-radius: 0 0 4px 0;
    z-index: 999;
    font-family: monospace;
    pointer-events: none;
}

/* Only show identifiers when enabled */
.section-identifiers-enabled .section-identifier {
    display: block;
}

/* Main section containers - light outline when section identifiers are enabled */
.section-identifiers-enabled .card,
.section-identifiers-enabled .container-fluid,
.section-identifiers-enabled .container,
.section-identifiers-enabled footer,
.section-identifiers-enabled .alert {
    position: relative;
    outline: 1px dashed rgba(13, 110, 253, 0.5);
}

/* Floating toggle button (only appears if no toggle is found in navbar) */
.section-identifiers-toggle {
    position: fixed;
    bottom: 10px;
    right: 10px;
    background-color: white;
    padding: 5px 10px;
    border-radius: 5px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    font-size: 12px;
}
```

## 3. JavaScript Implementation (`section-identifiers.js`)

```javascript
/**
 * Section Identifiers System
 * Adds sequential section numbers to main content containers
 * for development and support purposes
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Section Identifiers system');
    
    // Toggle button for section identifiers
    const toggleButton = document.getElementById('sectionIdentifiersToggle');
    if (!toggleButton) {
        console.log('Section identifiers toggle button not found');
        
        // Create a toggle button in the corner
        createToggleButton();
        return;
    }
    
    // Check if section identifiers should be enabled by default (from localStorage)
    const identifiersEnabled = localStorage.getItem('sectionIdentifiersEnabled') === 'true';
    toggleButton.checked = identifiersEnabled;
    
    // Apply the initial state
    if (identifiersEnabled) {
        document.body.classList.add('section-identifiers-enabled');
    }
    
    // Set up the section identifiers
    console.log('Setting up section identifiers');
    setupSectionIdentifiers();
    
    // Handle toggle changes
    toggleButton.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('section-identifiers-enabled');
            localStorage.setItem('sectionIdentifiersEnabled', 'true');
        } else {
            document.body.classList.remove('section-identifiers-enabled');
            localStorage.setItem('sectionIdentifiersEnabled', 'false');
        }
        
        // Refresh the identifiers
        setupSectionIdentifiers();
    });
    
    // Create a toggle button if one doesn't exist
    function createToggleButton() {
        // Create a floating toggle button
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'section-identifiers-toggle';
        
        const toggleBtn = document.createElement('div');
        toggleBtn.className = 'form-check form-switch';
        toggleBtn.innerHTML = `
            <input class="form-check-input" type="checkbox" id="sectionIdentifiersToggle">
            <label class="form-check-label small" for="sectionIdentifiersToggle">
                Section IDs
            </label>
        `;
        
        toggleContainer.appendChild(toggleBtn);
        document.body.appendChild(toggleContainer);
        
        // Get the new toggle button
        const newToggleButton = document.getElementById('sectionIdentifiersToggle');
        
        // Apply initial state
        const identifiersEnabled = localStorage.getItem('sectionIdentifiersEnabled') === 'true';
        newToggleButton.checked = identifiersEnabled;
        
        if (identifiersEnabled) {
            document.body.classList.add('section-identifiers-enabled');
        }
        
        // Handle toggle changes
        newToggleButton.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('section-identifiers-enabled');
                localStorage.setItem('sectionIdentifiersEnabled', 'true');
            } else {
                document.body.classList.remove('section-identifiers-enabled');
                localStorage.setItem('sectionIdentifiersEnabled', 'false');
            }
            
            // Refresh the identifiers
            setupSectionIdentifiers();
        });
        
        // Set up the identifiers
        setupSectionIdentifiers();
    }
    
    // Function to set up section identifiers
    function setupSectionIdentifiers() {
        // Remove any existing identifiers
        const existingIdentifiers = document.querySelectorAll('.section-identifier');
        existingIdentifiers.forEach(identifier => identifier.remove());
        
        // Skip adding identifiers if disabled
        if (!document.body.classList.contains('section-identifiers-enabled')) {
            return;
        }
        
        // Collect main content sections
        const sections = [];
        
        // Method 1: Find elements with specific class (preferred method if your app uses this)
        document.querySelectorAll('.section-container').forEach(container => {
            sections.push(container);
        });
        
        // Method 2: Find main content cards
        document.querySelectorAll('.card').forEach(card => {
            // Skip cards that are inside already identified sections
            if (card.closest('.section-container') === null) {
                sections.push(card);
            }
        });
        
        // Method 3: Find elements by headings
        document.querySelectorAll('h1, h2, h3, .card-header h5').forEach(heading => {
            const parentSection = heading.closest('section, .card, .container:not(.container-fluid)');
            if (parentSection && !sections.includes(parentSection)) {
                // Skip if this is inside an already identified section
                if (parentSection.closest('.section-container') === null) {
                    sections.push(parentSection);
                }
            }
        });
        
        // Method 4: Find elements by role or data attributes
        document.querySelectorAll('[role="main"], [role="region"], [data-section]').forEach(container => {
            if (!sections.includes(container)) {
                sections.push(container);
            }
        });
        
        // Filter out duplicates (in case a section was matched by multiple selectors)
        const uniqueSections = [...new Set(sections)];
        
        // Add sequential numbered identifiers
        uniqueSections.forEach((section, index) => {
            // Create the section identifier element
            const identifier = document.createElement('div');
            identifier.className = 'section-identifier';
            identifier.textContent = index + 1; // Start numbering from 1
            
            // Add the identifier to the container
            section.appendChild(identifier);
            
            // Make sure the container is positioned relatively
            if (getComputedStyle(section).position === 'static') {
                section.style.position = 'relative';
            }
        });
        
        console.log(`Added identifiers to ${uniqueSections.length} main sections`);
    }
});
```

## 4. Customization Options

### Adjusting the Appearance

To change the look of the section identifiers, modify the CSS:

```css
/* Custom colored section identifiers */
.section-identifier {
    /* Change to your preferred style */
    background-color: rgba(220, 53, 69, 0.8); /* Red */
    color: white;
    border-radius: 50%; /* Circle shape */
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    top: -8px;
    left: -8px;
}
```

### Custom Section Detection

To target specific elements in your application, modify the section collection logic:

```javascript
// Example for a custom app with specific structure
function setupSectionIdentifiers() {
    // ... existing code ...
    
    // Add application-specific selectors
    document.querySelectorAll('.my-app-widget').forEach(widget => {
        sections.push(widget);
    });
    
    // Add identifiers for specific content by heading text
    document.querySelectorAll('.card-header h5').forEach(heading => {
        const headingText = heading.textContent.trim();
        const card = heading.closest('.card');
        
        if (headingText.includes('My Widget')) {
            sections.push(card);
        }
    });
    
    // ... rest of the function ...
}
```

## 5. Implementation Notes

1. **No additional dependencies**: This implementation relies only on vanilla JavaScript.

2. **Automatic fallback**: The toggle will appear in a floating container if not found in your UI.

3. **Persistent state**: The user's preference is remembered between page loads.

4. **Non-intrusive**: The implementation won't affect your application functionality.

5. **Self-contained**: All related code is isolated in dedicated files.

By following this implementation pattern, you can add section identifiers to any web application without interfering with its normal operation.