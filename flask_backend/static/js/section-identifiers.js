/**
 * Section Identifiers System
 * Adds visual identifiers to page elements to help with template debugging
 * and enable easier component identification
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Section Identifiers system');
    
    // Toggle button for section identifiers
    const toggleButton = document.getElementById('sectionIdentifiersToggle');
    if (!toggleButton) {
        console.log('Section identifiers toggle button not found');
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
    
    // Function to set up section identifiers
    function setupSectionIdentifiers() {
        // Add section IDs to all container elements
        const containers = document.querySelectorAll('.container, .container-fluid');
        containers.forEach((container, index) => {
            container.setAttribute('data-section-id', `container-${index}`);
        });
        
        // Add section IDs to all cards
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.setAttribute('data-section-id', `card-${index}`);
        });
        
        // Add section IDs to all grid columns
        const columns = document.querySelectorAll('.row > div');
        columns.forEach((column, index) => {
            column.setAttribute('data-section-id', `col-${index}`);
        });
        
        // Add section IDs to navbar
        const navbars = document.querySelectorAll('.navbar');
        navbars.forEach((navbar, index) => {
            navbar.setAttribute('data-section-id', `navbar-${index}`);
        });
        
        // Add section IDs to alerts
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach((alert, index) => {
            alert.setAttribute('data-section-id', `alert-${index}`);
        });
        
        // Add section IDs to footer
        const footers = document.querySelectorAll('footer');
        footers.forEach((footer, index) => {
            footer.setAttribute('data-section-id', `footer-${index}`);
        });
    }
});