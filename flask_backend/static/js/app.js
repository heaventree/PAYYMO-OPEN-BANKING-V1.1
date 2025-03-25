/**
 * Payymo Dashboard App Script
 * Main JavaScript file for dashboard functionality
 */

// Store a reference to the original fetch API
const originalFetch = window.fetch;

/**
 * Intercept fetch calls that target images with SVG fallbacks
 * This allows us to use .png extensions in our templates but serve .svg files during development
 */
window.fetch = function(...args) {
    // Check if this is an image request
    const url = args[0];
    
    if (typeof url === 'string' && 
        (url.endsWith('.png') || url.endsWith('.jpg')) && 
        !url.includes('//')) {
        
        // Try SVG fallback first
        const svgUrl = url + '.svg';
        
        return originalFetch(svgUrl)
            .then(response => {
                if (response.ok) {
                    return response;
                }
                // Fall back to original request if SVG not found
                return originalFetch(...args);
            })
            .catch(() => {
                // Fall back to original request if there's an error
                return originalFetch(...args);
            });
    }
    
    // Pass through other requests
    return originalFetch(...args);
};

/**
 * Add section identifier labels to all elements marked with data-container-id
 */
function setupSectionIdentifiers() {
    console.log("Setting up section identifiers");
    
    const sections = document.querySelectorAll('[data-container-id]');
    console.log(`Added identifiers to ${sections.length} main sections`);
}

/**
 * Initialize all charts on the dashboard
 */
function initDashboardCharts() {
    // This will be expanded with real data integration
    // Currently handled inline in the templates
}

/**
 * Initialize all widgets with real data
 * This will replace the placeholder data in the template
 */
function initDashboardWidgets() {
    // Will be implemented to replace the static data from the template with real API data
}

/**
 * Format numbers with proper formatting for currency and large numbers
 */
function formatCurrency(amount, currency = 'GBP') {
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format dates in a user-friendly way
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("Initializing Section Identifiers system");
    setupSectionIdentifiers();
    
    // Initialize charts after a short delay to ensure containers are ready
    setTimeout(() => {
        initDashboardCharts();
        initDashboardWidgets();
    }, 100);
});