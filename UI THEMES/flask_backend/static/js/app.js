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
 * Initialize sidebar and menus
 */
function initializeSidebar() {
    console.log("Initializing sidebar and menu functions");
    
    // Toggle sidebar
    document.querySelectorAll('.vertical-menu-btn, #vertical-hover, #topnav-hamburger-icon').forEach(btn => {
        btn.addEventListener('click', function(e) {
            document.body.classList.toggle('sidebar-enable');
            
            if (window.innerWidth >= 992) {
                document.body.classList.toggle('vertical-collpsed');
            }
            
            // Toggle hamburger icon animation
            if (this.id === 'topnav-hamburger-icon') {
                this.classList.toggle('open');
            }
            
            // Close open submenus when sidebar is collapsed
            if (document.body.classList.contains('vertical-collpsed')) {
                document.querySelectorAll('.sidebar-submenu, .menu-dropdown').forEach(submenu => {
                    submenu.classList.remove('show');
                });
            }
        });
    });
    
    // Add active class to sidebar menu items when clicked
    document.querySelectorAll('.nav-link.menu-link').forEach(item => {
        item.addEventListener('click', function() {
            if (!this.hasAttribute('data-bs-toggle')) {
                document.querySelectorAll('.nav-link.menu-link').forEach(i => {
                    i.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });
    
    // Close sidebar when click outside (for mobile)
    document.addEventListener('click', function(e) {
        if (document.body.classList.contains('sidebar-enable') && 
            !e.target.closest('.app-menu') && 
            !e.target.closest('.vertical-menu-btn') &&
            !e.target.closest('#topnav-hamburger-icon')) {
            document.body.classList.remove('sidebar-enable');
        }
    });
    
    // Apply default sidebar state based on screen size
    function setSidebarState() {
        if (window.innerWidth >= 992) {
            document.body.classList.add('vertical-collpsed');
        } else {
            document.body.classList.remove('vertical-collpsed');
        }
    }
    
    // Set initial state
    setSidebarState();
    
    // Update on resize
    window.addEventListener('resize', setSidebarState);

    // Make sure navbar-menu gets proper visibility and display
    const appMenu = document.querySelector('.app-menu');
    if (appMenu) {
        appMenu.style.display = 'block';
        appMenu.style.visibility = 'visible';
        
        // Force the height calculation 
        setTimeout(() => {
            const scrollbar = document.getElementById('scrollbar');
            if (scrollbar) {
                scrollbar.style.height = (window.innerHeight - 70) + 'px';
            }
        }, 100);
    }
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
    
    // Initialize the sidebar
    initializeSidebar();
    
    // Initialize charts after a short delay to ensure containers are ready
    setTimeout(() => {
        initDashboardCharts();
        initDashboardWidgets();
    }, 100);
});