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
        toggleContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toggleContainer.style.zIndex = '1050';
        
        const toggleBtn = document.createElement('div');
        toggleBtn.className = 'form-check form-switch bg-white p-2 rounded shadow-sm';
        toggleBtn.innerHTML = `
            <input class="form-check-input" type="checkbox" id="sectionIdentifiersToggle">
            <label class="form-check-label small" for="sectionIdentifiersToggle">
                <i class="fas fa-th me-1"></i>
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
        
        // Add the color legend
        addSectionLegend();
    }
    
    // Function to set up section identifiers
    function setupSectionIdentifiers() {
        // Global counter for sequential numbering
        let sectionCounter = 1;
        
        // Add sequential IDs to all major layout elements
        const layoutElements = {
            'container': document.querySelectorAll('.container, .container-fluid'),
            'card': document.querySelectorAll('.card'),
            'col': document.querySelectorAll('.row > div'),
            'navbar': document.querySelectorAll('.navbar'),
            'alert': document.querySelectorAll('.alert'),
            'footer': document.querySelectorAll('footer'),
            'table': document.querySelectorAll('.table, .table-responsive'),
            'form': document.querySelectorAll('form')
        };
        
        // Count total elements for logging
        let totalElements = 0;
        
        // Process each element type
        Object.entries(layoutElements).forEach(([type, elements]) => {
            elements.forEach((element) => {
                // Skip if already has a section ID
                if (element.hasAttribute('data-section-id')) {
                    return;
                }
                
                // Create a sequential ID that includes the element type
                element.setAttribute('data-section-id', `${type}-${sectionCounter}`);
                
                // Also add a simple numeric ID for quick reference
                element.setAttribute('data-section-num', `${sectionCounter}`);
                
                // Increment the counter
                sectionCounter++;
                totalElements++;
            });
        });
        
        console.log(`Added identifiers to ${totalElements} sections`);
    }
    
    // Function to add a color legend
    function addSectionLegend() {
        // Remove existing legend if any
        const existingLegend = document.querySelector('.section-identifiers-legend');
        if (existingLegend) {
            existingLegend.remove();
        }
        
        // Create the legend
        const legend = document.createElement('div');
        legend.className = 'section-identifiers-legend';
        
        // Define the color codes and element types
        const colorCodes = [
            { type: 'Container', color: 'rgba(13, 110, 253, 0.7)' },
            { type: 'Card', color: 'rgba(25, 135, 84, 0.7)' },
            { type: 'Column', color: 'rgba(220, 53, 69, 0.7)' },
            { type: 'Navbar', color: 'rgba(255, 193, 7, 0.7)' },
            { type: 'Alert', color: 'rgba(13, 202, 240, 0.7)' },
            { type: 'Footer', color: 'rgba(108, 117, 125, 0.7)' },
            { type: 'Table', color: 'rgba(111, 66, 193, 0.7)' },
            { type: 'Form', color: 'rgba(253, 126, 20, 0.7)' }
        ];
        
        // Create the legend title
        const title = document.createElement('h6');
        title.className = 'mb-2';
        title.textContent = 'Section Types';
        legend.appendChild(title);
        
        // Create the legend items
        const list = document.createElement('div');
        list.className = 'mb-0';
        
        colorCodes.forEach(({ type, color }) => {
            const item = document.createElement('div');
            item.className = 'mb-1 d-flex align-items-center';
            
            const colorBox = document.createElement('span');
            colorBox.style.cssText = `
                display: inline-block;
                width: 12px;
                height: 12px;
                background-color: ${color};
                margin-right: 6px;
                border-radius: 2px;
            `;
            
            const typeName = document.createElement('span');
            typeName.className = 'small';
            typeName.textContent = type;
            
            item.appendChild(colorBox);
            item.appendChild(typeName);
            list.appendChild(item);
        });
        
        legend.appendChild(list);
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'btn btn-sm btn-outline-secondary w-100 mt-2';
        closeBtn.textContent = 'Close Legend';
        closeBtn.addEventListener('click', () => {
            legend.style.display = 'none';
        });
        
        legend.appendChild(closeBtn);
        
        // Add the legend to the page
        document.body.appendChild(legend);
    }
});