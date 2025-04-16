/**
 * Theme Switcher
 * Manages light/dark mode switching and preferences
 */

(function() {
    'use strict';
    
    // Theme constants
    const LIGHT_MODE = 'light';
    const DARK_MODE = 'dark';
    const THEME_STORAGE_KEY = 'payymo-theme-preference';
    
    /**
     * Set theme on HTML element
     */
    function setTheme(theme) {
        const oldTheme = document.documentElement.getAttribute('data-bs-theme');
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem(THEME_STORAGE_KEY, theme);
        
        // Dispatch theme changed event if theme has changed
        if (oldTheme !== theme) {
            window.dispatchEvent(new CustomEvent('themeChanged', {
                detail: {
                    oldTheme: oldTheme,
                    newTheme: theme
                }
            }));
        }
    }
    
    /**
     * Get user's preferred theme
     */
    function getPreferredTheme() {
        // Check localStorage
        const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (storedTheme) {
            return storedTheme;
        }
        
        // Check system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 
            DARK_MODE : LIGHT_MODE;
    }
    
    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === DARK_MODE ? LIGHT_MODE : DARK_MODE;
        setTheme(newTheme);
    }
    
    /**
     * Initialize theme switcher
     */
    function initThemeSwitcher() {
        // Set initial theme
        const theme = getPreferredTheme();
        setTheme(theme);
        
        // Find theme switchers in DOM
        const themeSwitchers = document.querySelectorAll('.theme-switcher');
        
        // Add event listeners to switchers
        themeSwitchers.forEach(switcher => {
            const input = switcher.querySelector('input[type="checkbox"]');
            if (input) {
                input.checked = theme === DARK_MODE;
                
                input.addEventListener('change', function() {
                    setTheme(this.checked ? DARK_MODE : LIGHT_MODE);
                });
            }
        });
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (localStorage.getItem(THEME_STORAGE_KEY)) return; // User has a preference, don't override
            setTheme(e.matches ? DARK_MODE : LIGHT_MODE);
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeSwitcher);
    } else {
        initThemeSwitcher();
    }
    
    // Expose functions to global scope
    window.ThemeSwitcher = {
        toggle: toggleTheme,
        setTheme: setTheme,
        getTheme: function() {
            return document.documentElement.getAttribute('data-bs-theme');
        }
    };
})(); 