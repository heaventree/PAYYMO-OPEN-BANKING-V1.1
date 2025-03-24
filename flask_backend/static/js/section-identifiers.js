/**
 * Section Identifiers System
 * Adds sequential numbered identifiers to main containers
 * Each set of related cards/panes has its own container
 * Based on the WHMCS addon approach
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Section Identifiers system');
    
    // Toggle button for section identifiers
    const toggleButton = document.getElementById('sectionIdentifiersToggle');
    if (!toggleButton) {
        console.log('Section identifiers toggle button not found');
        
        // Create a toggle button in the corner if one doesn't exist
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
        });
        
        // Set up the identifiers
        setupSectionIdentifiers();
    }
    
    // Function to set up section identifiers
    function setupSectionIdentifiers() {
        // Remove any existing identifiers
        const existingIdentifiers = document.querySelectorAll('.section-identifier');
        existingIdentifiers.forEach(identifier => identifier.remove());
        
        // Only select the main containers (parent containers that group related cards)
        // Use direct children of main content area to avoid selecting nested containers
        const mainContentArea = document.querySelector('main') || document.body;
        const topLevelContainers = Array.from(mainContentArea.children).filter(el => {
            return (
                el.classList.contains('container') || 
                el.classList.contains('container-fluid') ||
                (el.tagName === 'DIV' && el.querySelector('.card, .alert, .row'))
            );
        });
        
        // Add sequential numbered identifiers
        topLevelContainers.forEach((container, index) => {
            // Create the section identifier element
            const identifier = document.createElement('div');
            identifier.className = 'section-identifier';
            identifier.textContent = index + 1; // Start numbering from 1
            
            // Add the identifier to the container
            container.appendChild(identifier);
            
            // Make sure the container is positioned relatively
            if (getComputedStyle(container).position === 'static') {
                container.style.position = 'relative';
            }
        });
        
        // Also add identifiers to alert boxes that might be direct children of the body
        const alertContainers = document.querySelectorAll('.alert:not(.section-identifier)');
        alertContainers.forEach((alert, index) => {
            // Skip alerts that are inside already marked containers
            if (alert.closest('[class*="container"]')) {
                return;
            }
            
            const identifier = document.createElement('div');
            identifier.className = 'section-identifier';
            identifier.textContent = topLevelContainers.length + index + 1;
            
            alert.appendChild(identifier);
            
            if (getComputedStyle(alert).position === 'static') {
                alert.style.position = 'relative';
            }
        });
        
        console.log(`Added identifiers to ${topLevelContainers.length} main containers`);
    }
});