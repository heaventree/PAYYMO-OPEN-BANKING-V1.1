/**
 * Section Identifiers Manager
 * Provides a modular system for adding numbered section identifiers to UI elements
 * Can be toggled on/off and persists state via cookies
 */

const SectionIdentifiers = {
    // Configuration
    enabled: false,
    cookieName: 'section_identifiers_enabled',
    cookieExpireDays: 30,
    
    // Initialize the system
    init: function() {
        console.log("Initializing Section Identifiers system");
        // Check saved preference
        this.loadPreference();
        
        // Setup toggle switch in navbar
        this.setupToggleSwitch();
        
        // Set initial state based on preference
        this.applyState();
        
        // Set up mutation observer to handle dynamically loaded content
        this.setupObserver();
    },
    
    // Create and add identifiers to sections
    setupIdentifiers: function() {
        console.log("Setting up section identifiers");
        
        // Remove any existing identifiers first
        document.querySelectorAll('.section-identifier').forEach(el => el.remove());
        
        // If not enabled, don't add new ones
        if (!this.enabled) return;
        
        // Select elements with section-container class
        const containers = document.querySelectorAll('.section-container');
        
        // Add numbered badges
        containers.forEach((container, index) => {
            const identifier = document.createElement('span');
            identifier.className = 'section-identifier badge';
            identifier.textContent = (index + 1).toString();
            container.prepend(identifier);
            
            // Add section ID as attribute if it doesn't exist
            if (!container.id || !container.id.startsWith('section-')) {
                container.id = `section-${index + 1}`;
            }
            
            // Add comment tag to help identify in HTML
            const sectionComment = document.createComment(` Section ${index + 1} Start `);
            container.parentNode.insertBefore(sectionComment, container);
            
            // Mark end of section with comment
            const endComment = document.createComment(` Section ${index + 1} End `);
            container.parentNode.insertBefore(endComment, container.nextSibling);
        });
        
        console.log(`Added identifiers to ${containers.length} sections`);
    },
    
    // Toggle identifiers on/off
    toggle: function() {
        this.enabled = !this.enabled;
        this.savePreference();
        this.applyState();
        
        // Show confirmation
        if (typeof showToast === 'function') {
            showToast(
                `Section identifiers ${this.enabled ? 'enabled' : 'disabled'}`,
                this.enabled ? 'success' : 'info'
            );
        }
    },
    
    // Apply current state
    applyState: function() {
        // Add or remove the body class
        if (this.enabled) {
            document.body.classList.add('show-section-identifiers');
        } else {
            document.body.classList.remove('show-section-identifiers');
        }
        
        // Setup or remove identifiers
        this.setupIdentifiers();
        
        // Update toggle switch state
        const toggleSwitch = document.getElementById('sectionIdentifiersToggle');
        if (toggleSwitch) {
            toggleSwitch.checked = this.enabled;
        }
        
        // Update toggle button state (for help menu if it exists)
        const toggleBtn = document.getElementById('toggleSectionIdentifiers');
        if (toggleBtn) {
            toggleBtn.innerHTML = `
                <i class="fas fa-${this.enabled ? 'eye-slash' : 'eye'} me-2"></i>
                ${this.enabled ? 'Hide' : 'Show'} Section Numbers
            `;
        }
    },
    
    // Setup toggle switch in navbar
    setupToggleSwitch: function() {
        const toggleSwitch = document.getElementById('sectionIdentifiersToggle');
        if (!toggleSwitch) return;
        
        // Set initial state
        toggleSwitch.checked = this.enabled;
        
        // Add click event listener
        toggleSwitch.addEventListener('change', () => this.toggle());
    },
    
    // Save preference to cookie
    savePreference: function() {
        const expires = new Date();
        expires.setDate(expires.getDate() + this.cookieExpireDays);
        document.cookie = `${this.cookieName}=${this.enabled}; expires=${expires.toUTCString()}; path=/`;
    },
    
    // Load preference from cookie
    loadPreference: function() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith(this.cookieName + '='));
            
        if (cookieValue) {
            this.enabled = cookieValue.split('=')[1] === 'true';
        }
    },
    
    // Add toggle button to help menu
    addToggleButton: function() {
        const helpMenu = document.querySelector('.help-menu');
        if (!helpMenu) return;
        
        // Check if button already exists
        if (document.getElementById('toggleSectionIdentifiers')) return;
        
        // Create toggle button
        const toggleItem = document.createElement('li');
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'dropdown-item';
        toggleBtn.id = 'toggleSectionIdentifiers';
        toggleBtn.innerHTML = `
            <i class="fas fa-${this.enabled ? 'eye-slash' : 'eye'} me-2"></i>
            ${this.enabled ? 'Hide' : 'Show'} Section Numbers
        `;
        toggleBtn.addEventListener('click', () => this.toggle());
        
        toggleItem.appendChild(toggleBtn);
        helpMenu.appendChild(toggleItem);
    },
    
    // Setup mutation observer for dynamic content
    setupObserver: function() {
        const observer = new MutationObserver(mutations => {
            let shouldUpdate = false;
            
            // Check if relevant content was added/removed
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if any added nodes have section-container class or contain elements with it
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.classList && node.classList.contains('section-container')) {
                                shouldUpdate = true;
                            } else if (node.querySelector && node.querySelector('.section-container')) {
                                shouldUpdate = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldUpdate && this.enabled) {
                // Update identifiers when new containers are added
                this.setupIdentifiers();
            }
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
};

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize with a small delay to allow other scripts to load
    setTimeout(() => SectionIdentifiers.init(), 500);
});