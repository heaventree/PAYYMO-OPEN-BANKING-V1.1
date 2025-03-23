/**
 * Card Style Switcher
 * This script controls the card styling toggle functionality
 * Provides options for clean (borderless) vs colored card styles
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find the toggle switch
    const cardStyleToggle = document.getElementById('card-style-switcher');
    if (!cardStyleToggle) return;

    // Check for saved preference
    const savedPreference = localStorage.getItem('card-style-preference');
    const useCleanStyle = savedPreference === 'clean';
    
    // Set initial state based on preference 
    // Note: The checkbox is checked for colored style, unchecked for clean
    cardStyleToggle.checked = !useCleanStyle;

    // Apply initial style
    applyCardStyle(!cardStyleToggle.checked);

    // Add toggle event listener
    cardStyleToggle.addEventListener('change', function() {
        // Apply style (clean if unchecked, colored if checked)
        applyCardStyle(!this.checked);
        
        // Save preference
        localStorage.setItem('card-style-preference', !this.checked ? 'clean' : 'colored');
        
        // Show feedback
        showToast(
            !this.checked ? 
            'Using clean card style with no accent colors' : 
            'Using colored card style with accent colors', 
            'info'
        );
    });

    /**
     * Apply card style to all cards
     * @param {boolean} useCleanStyle - Whether to use the clean style or colored style
     */
    function applyCardStyle(useCleanStyle) {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            if (useCleanStyle) {
                // Add clean style class and remove any colored top borders
                card.classList.add('card-clean');
                
                // Remove border-top classes that might exist
                card.classList.remove(
                    'border-top-primary', 
                    'border-top-secondary', 
                    'border-top-success', 
                    'border-top-danger', 
                    'border-top-warning', 
                    'border-top-info', 
                    'border-top-dark'
                );
            } else {
                // Remove clean style
                card.classList.remove('card-clean');
                
                // Determine appropriate colored border based on card content
                applyCardColoring(card);
            }
        });
    }

    /**
     * Apply card coloring based on card content and purpose
     * @param {Element} card - The card element to color
     */
    function applyCardColoring(card) {
        // Default color
        let colorClass = 'border-top-secondary';
        
        // Determine color by title or content
        if (card.querySelector('.card-title')) {
            const title = card.querySelector('.card-title').innerText.toLowerCase();
            
            if (title.includes('transaction') || title.includes('payment')) {
                colorClass = 'border-top-primary';
            } else if (title.includes('bank') || title.includes('connection')) {
                colorClass = 'border-top-info';
            } else if (title.includes('invoice') || title.includes('match')) {
                colorClass = 'border-top-success';
            } else if (title.includes('alert') || title.includes('error')) {
                colorClass = 'border-top-danger';
            } else if (title.includes('summary') || title.includes('overview')) {
                colorClass = 'border-top-dark';
            } else if (title.includes('goal') || title.includes('target')) {
                colorClass = 'border-top-warning';
            }
        }
        
        // Check for common card types by CSS classes or content
        if (card.classList.contains('goal-card')) {
            colorClass = 'border-top-warning';
        } else if (card.classList.contains('financial-summary')) {
            colorClass = 'border-top-dark';
        } else if (card.classList.contains('stripe-card') || 
                   card.querySelector('[data-provider="stripe"]')) {
            colorClass = 'border-top-primary';
        } else if (card.classList.contains('bank-card') || 
                   card.querySelector('[data-provider="gocardless"]')) {
            colorClass = 'border-top-info';
        }
        
        // Apply the color class
        card.classList.add(colorClass);
    }
});