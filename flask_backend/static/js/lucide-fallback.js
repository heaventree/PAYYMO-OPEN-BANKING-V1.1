/**
 * Lucide Icons Fallback Script
 *
 * This script ensures Lucide icons will load even if the primary 
 * source fails. It checks if the Lucide library is already loaded,
 * and if not, loads it from an alternative CDN.
 */
(function() {
    // Check if Lucide is already defined
    if (typeof lucide === 'undefined') {
        console.log('Lucide not loaded, attempting fallback...');
        
        // Create a new script element
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js';
        script.async = true;
        
        // Add loading error handler
        script.onerror = function() {
            console.error('Failed to load Lucide from fallback CDN');
        };
        
        // Add onload handler to initialize icons once loaded
        script.onload = function() {
            console.log('Lucide loaded from fallback CDN');
            if (typeof lucide !== 'undefined') {
                // Create icons once library is loaded
                lucide.createIcons();
                
                // Handle icon replacements as in main script
                const iconReplacements = {
                    'building-bank': 'building',
                    'landmark': 'home',
                    'layout-dashboard': 'layout',
                    'link-off': 'unlink'
                };
                
                // Apply replacements
                Object.entries(iconReplacements).forEach(([original, replacement]) => {
                    document.querySelectorAll(`[data-lucide="${original}"]`).forEach(icon => {
                        icon.setAttribute('data-lucide', replacement);
                    });
                });
                
                // Create icons again to apply changes
                lucide.createIcons();
            }
        };
        
        // Add the script to the document head
        document.head.appendChild(script);
    }
})();