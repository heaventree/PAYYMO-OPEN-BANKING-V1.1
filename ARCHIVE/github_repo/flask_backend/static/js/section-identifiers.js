/**
 * Section Identifiers System for Payymo
 * Based exactly on the original WHMCS implementation
 * Adds sequential section numbers to main content containers
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
    
    // Function to set up section identifiers - WHMCS style exactly
    function setupSectionIdentifiers() {
        // Remove any existing identifiers
        const existingIdentifiers = document.querySelectorAll('.section-identifier');
        existingIdentifiers.forEach(identifier => identifier.remove());
        
        // Get all the main rows that contain our content sections
        const contentRows = document.querySelectorAll('.row');
        
        // WHMCS addon style - select each main content section
        const sections = [];
        
        // Section 1: Welcome card - first card in the first row
        if (contentRows.length > 0) {
            const welcomeCard = contentRows[0].querySelector('.card');
            if (welcomeCard) sections.push(welcomeCard);
        }
        
        // Section 2: Stats row - the row with the 4 stat cards (usually 2nd row)
        if (contentRows.length > 1) {
            const statsRow = contentRows[1]; // Second row with stats
            
            // Check if this row has the stat cards by looking for col-xl-3
            const hasStatCards = statsRow.querySelector('.col-xl-3') !== null;
            if (hasStatCards) sections.push(statsRow);
        }
        
        // Section 3-5: Cards with headings
        document.querySelectorAll('.card-header h5').forEach(heading => {
            const headingText = heading.textContent.trim();
            const card = heading.closest('.card');
            
            if (headingText.includes('Recent Transactions')) {
                sections.push(card); // Section 3
            } else if (headingText.includes('Recent Invoices')) {
                sections.push(card); // Section 4
            } else if (headingText.includes('Integrations') || headingText.includes('Your Integrations')) {
                sections.push(card); // Section 5
            }
        });
        
        // Filter out any null sections
        const validSections = sections.filter(section => section !== null);
        
        // Add sequential numbered identifiers
        validSections.forEach((section, index) => {
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
        
        console.log(`Added identifiers to ${validSections.length} main sections`);
    }
});