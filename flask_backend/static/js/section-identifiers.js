/**
 * Section Identifiers System
 * Adds sequential numbered identifiers to main page containers
 * Based on the simple WHMCS addon approach
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
        
        // Select only main containers (not all elements)
        const containers = document.querySelectorAll('.container, .container-fluid, .card, .alert');
        
        // Add sequential numbered identifiers
        containers.forEach((container, index) => {
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
        
        console.log(`Added identifiers to ${containers.length} containers`);
    }
});