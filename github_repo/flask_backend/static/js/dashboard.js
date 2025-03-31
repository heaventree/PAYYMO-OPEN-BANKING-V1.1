/**
 * Payymo Dashboard UI Utilities
 * 
 * This file contains utility functions for rendering charts and handling
 * UI interactions across the dashboard.
 */

// Theme management
function initTheme() {
    // Check for saved theme preference or use default
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    
    // Update UI elements for theme
    const themeTogglers = document.querySelectorAll('.theme-toggle');
    if (themeTogglers.length) {
        themeTogglers.forEach(toggler => {
            toggler.checked = savedTheme === 'dark';
            toggler.addEventListener('change', () => {
                const newTheme = toggler.checked ? 'dark' : 'light';
                document.documentElement.setAttribute('data-bs-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateChartsForTheme(newTheme);
            });
        });
    }
}

// Charts configuration
const chartColors = {
    primary: '#0dcaf0',
    success: '#198754',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#0dcaf0',
    dark: {
        gridColor: 'rgba(255, 255, 255, 0.05)',
        textColor: '#adb5bd'
    },
    light: {
        gridColor: 'rgba(0, 0, 0, 0.05)',
        textColor: '#495057'
    }
};

// Update chart styling based on theme
function updateChartsForTheme(theme) {
    // Set chart defaults based on theme
    Chart.defaults.color = theme === 'dark' ? chartColors.dark.textColor : chartColors.light.textColor;
    
    // Update all active charts
    Chart.instances.forEach(chart => {
        // Update grid colors
        if (chart.config.options.scales && chart.config.options.scales.y) {
            chart.config.options.scales.y.grid.color = theme === 'dark' ? 
                chartColors.dark.gridColor : 
                chartColors.light.gridColor;
        }
        
        // Update the chart
        chart.update();
    });
}

// Transaction Chart
function createTransactionChart(elementId, labels, data) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    const theme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
    const gridColor = theme === 'dark' ? chartColors.dark.gridColor : chartColors.light.gridColor;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Transactions',
                data: data,
                borderColor: chartColors.primary,
                backgroundColor: `${chartColors.primary}20`,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: theme === 'dark' ? '#343a40' : '#ffffff',
                    titleColor: theme === 'dark' ? '#ffffff' : '#212529',
                    bodyColor: theme === 'dark' ? '#adb5bd' : '#495057',
                    borderColor: theme === 'dark' ? '#495057' : '#dee2e6',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false
                }
            }
        }
    });
}

// Income Distribution Chart (Pie/Doughnut)
function createIncomeDistributionChart(elementId, labels, data) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    const theme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    chartColors.primary,
                    chartColors.success,
                    chartColors.warning,
                    chartColors.info,
                    '#6f42c1',
                    '#fd7e14'
                ],
                borderWidth: 5,
                borderColor: theme === 'dark' ? '#212529' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    backgroundColor: theme === 'dark' ? '#343a40' : '#ffffff',
                    titleColor: theme === 'dark' ? '#ffffff' : '#212529',
                    bodyColor: theme === 'dark' ? '#adb5bd' : '#495057',
                    borderColor: theme === 'dark' ? '#495057' : '#dee2e6',
                    borderWidth: 1,
                    padding: 10
                }
            },
            cutout: '70%'
        }
    });
}

// Interactive elements setup
function setupInteractiveElements() {
    // Setup toast notifications
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(toast => {
        new bootstrap.Toast(toast, { 
            delay: 5000 
        });
    });
    
    // Setup popovers
    const popoverTriggers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverTriggers.forEach(trigger => {
        new bootstrap.Popover(trigger);
    });
    
    // Setup tooltips
    const tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggers.forEach(trigger => {
        new bootstrap.Tooltip(trigger);
    });
    
    // Add notification popup functionality
    const notificationBtn = document.getElementById('notification-toggle');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', () => {
            // Show notification dropdown, etc.
        });
    }
}

// Data refresh functionality
function setupDataRefresh() {
    const refreshButtons = document.querySelectorAll('.refresh-data');
    
    refreshButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Add spinning animation to button
            const icon = button.querySelector('i');
            if (icon) {
                icon.classList.add('fa-spin');
                button.disabled = true;
            }
            
            // Simulate data refresh (in real app, this would be an API call)
            setTimeout(() => {
                if (icon) {
                    icon.classList.remove('fa-spin');
                    button.disabled = false;
                }
                
                // Show success toast
                const toast = document.getElementById('refresh-toast');
                if (toast) {
                    const toastInstance = new bootstrap.Toast(toast);
                    toastInstance.show();
                }
            }, 1500);
        });
    });
}

// Initialize everything when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();
    
    // Setup interactive elements
    setupInteractiveElements();
    
    // Setup data refresh
    setupDataRefresh();
    
    // Set up mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside (mobile)
        document.addEventListener('click', function(event) {
            if (window.innerWidth < 992 && 
                !sidebar.contains(event.target) && 
                !sidebarToggle.contains(event.target) && 
                sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
    }
}); 