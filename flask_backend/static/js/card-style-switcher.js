/**
 * Card Style Switcher
 * A utility for toggling between different card style variations
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if the toggle button exists
    const styleSwitcher = document.getElementById('card-style-switcher');
    if (!styleSwitcher) return;
    
    // Initialize based on saved preference
    const useColoredCards = localStorage.getItem('useColoredCards') !== 'false'; // default to true
    updateCardStyles(useColoredCards);
    styleSwitcher.checked = useColoredCards;
    
    // Add event listener for the toggle
    styleSwitcher.addEventListener('change', function(e) {
        const useColored = e.target.checked;
        updateCardStyles(useColored);
        localStorage.setItem('useColoredCards', useColored);
    });
    
    /**
     * Update card styles across the page
     * @param {boolean} useColoredStyles - Whether to use colored card styles
     */
    function updateCardStyles(useColoredStyles) {
        // Apply styles to all cards
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            if (useColoredStyles) {
                // Check if the card already has a specific color class
                const hasColorClass = Array.from(card.classList).some(cls => cls.startsWith('card-') && cls !== 'card-body' && cls !== 'card-header' && cls !== 'card-footer' && cls !== 'card-title' && cls !== 'card-clean');
                
                // If no color class, add the default primary color
                if (!hasColorClass) {
                    card.classList.add('card-primary');
                }
                
                // Remove the clean class if present
                card.classList.remove('card-clean');
            } else {
                // Store the current color class, if any
                const colorClass = Array.from(card.classList).find(cls => cls.startsWith('card-') && cls !== 'card-body' && cls !== 'card-header' && cls !== 'card-footer' && cls !== 'card-title' && cls !== 'card-clean');
                
                // Remove the color class
                if (colorClass) {
                    card.classList.remove(colorClass);
                }
                
                // Add the clean class
                card.classList.add('card-clean');
            }
        });
    }
});