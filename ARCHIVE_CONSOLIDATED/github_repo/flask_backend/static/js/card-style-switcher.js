/**
 * Card Style Switcher
 * Allows toggling between colored cards and standard white cards
 */
document.addEventListener('DOMContentLoaded', function() {
    // Toggle switch for card styles
    const cardStyleToggle = document.getElementById('card-style-switcher');
    if (!cardStyleToggle) return;
    
    // Check if user has a preference stored
    const coloredCardsEnabled = localStorage.getItem('coloredCardsEnabled') !== 'false'; // Default to true
    
    // Set initial state
    cardStyleToggle.checked = coloredCardsEnabled;
    
    // Apply initial styles
    if (!coloredCardsEnabled) {
        document.querySelectorAll('.card.bg-primary, .card.bg-success, .card.bg-warning, .card.bg-info, .card.bg-danger')
            .forEach(card => {
                // Store the original classes for later restoration
                card.setAttribute('data-original-bg', card.className.match(/(bg-\w+(-opacity-\d+)?)/g).join(' '));
                // Remove background color classes
                card.className = card.className.replace(/bg-\w+(-opacity-\d+)?/g, '');
            });
    }
    
    // Listen for toggle changes
    cardStyleToggle.addEventListener('change', function() {
        if (this.checked) {
            // Enable colored cards
            document.querySelectorAll('.card[data-original-bg]').forEach(card => {
                // Restore original background classes
                const originalBg = card.getAttribute('data-original-bg');
                if (originalBg) {
                    card.className += ' ' + originalBg;
                }
            });
            localStorage.setItem('coloredCardsEnabled', 'true');
        } else {
            // Disable colored cards
            document.querySelectorAll('.card.bg-primary, .card.bg-success, .card.bg-warning, .card.bg-info, .card.bg-danger')
                .forEach(card => {
                    // Store the original classes for later restoration
                    card.setAttribute('data-original-bg', card.className.match(/(bg-\w+(-opacity-\d+)?)/g).join(' '));
                    // Remove background color classes
                    card.className = card.className.replace(/bg-\w+(-opacity-\d+)?/g, '');
                });
            localStorage.setItem('coloredCardsEnabled', 'false');
        }
    });
});