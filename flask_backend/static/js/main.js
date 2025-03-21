document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips (safely)
    try {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        if (typeof bootstrap !== 'undefined') {
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    } catch (e) {
        console.log('Bootstrap tooltip initialization skipped');
    }

    // Initialize Bootstrap popovers (safely)
    try {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        if (typeof bootstrap !== 'undefined') {
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }
    } catch (e) {
        console.log('Bootstrap popover initialization skipped');
    }

    // Handle sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed'));
        });

        // Restore sidebar state from local storage
        if (localStorage.getItem('sidebar-collapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
        }
    }

    // Handle data refresh buttons
    const refreshButtons = document.querySelectorAll('.btn-refresh');
    refreshButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-refresh-target');
            if (target) {
                refreshData(target);
            }
        });
    });

    // Initialize charts if they exist
    initializeCharts();
    
    // Initialize data tables
    initializeDataTables();
    
    // Set up active tab persistence
    const tabs = document.querySelectorAll('a[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const id = e.target.getAttribute('href').substr(1);
            localStorage.setItem('activeTab', id);
        });
    });
    
    // Restore active tab from localStorage
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        const tab = document.querySelector(`a[href="#${activeTab}"]`);
        if (tab) {
            const bsTab = new bootstrap.Tab(tab);
            bsTab.show();
        }
    }
});

// Function to refresh data sections
function refreshData(target) {
    const container = document.getElementById(target);
    if (!container) return;
    
    const spinnerHtml = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Refreshing data...</p>
        </div>
    `;
    
    container.innerHTML = spinnerHtml;
    
    // In a real application, this would make an AJAX request to get fresh data
    fetch(`/api/refresh/${target}`)
        .then(response => response.json())
        .then(data => {
            // Update the container with new data
            // This would be implemented based on the specific data structure
            container.innerHTML = data.html || 'Data refreshed';
        })
        .catch(error => {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="feather icon-alert-circle"></i> 
                    Error refreshing data: ${error.message}
                </div>
            `;
        });
}

// Initialize charts using Chart.js
function initializeCharts() {
    // Check if Chart is defined
    if (typeof Chart === 'undefined') {
        console.log('Chart.js not loaded, skipping chart initialization');
        return;
    }
    
    // Transaction Stats Chart
    const transactionStatsElem = document.getElementById('transactionStats');
    if (transactionStatsElem) {
        try {
            const ctx = transactionStatsElem.getContext('2d');
            
            // Get data from data attributes
            const labels = JSON.parse(transactionStatsElem.getAttribute('data-labels') || '[]');
            const amounts = JSON.parse(transactionStatsElem.getAttribute('data-amounts') || '[]');
            const counts = JSON.parse(transactionStatsElem.getAttribute('data-counts') || '[]');
            
            new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Amount',
                        yAxisID: 'y-axis-1',
                        data: amounts,
                        backgroundColor: 'rgba(79, 70, 229, 0.6)',
                        borderColor: 'rgba(79, 70, 229, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Count',
                        yAxisID: 'y-axis-2',
                        data: counts,
                        type: 'line',
                        fill: false,
                        backgroundColor: 'rgba(147, 51, 234, 0.6)',
                        borderColor: 'rgba(147, 51, 234, 1)',
                        borderWidth: 2,
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    'y-axis-1': {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Amount'
                        }
                    },
                    'y-axis-2': {
                        type: 'linear',
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    }
                }
            }
        });
        } catch (error) {
            console.error("Error initializing transaction chart:", error);
        }
    }
    
    // Match Rate Chart
    const matchRateElem = document.getElementById('matchRateChart');
    if (matchRateElem) {
        try {
            const ctx = matchRateElem.getContext('2d');
            
            // Get data from data attributes
            const matched = parseInt(matchRateElem.getAttribute('data-matched') || '0');
            const unmatched = parseInt(matchRateElem.getAttribute('data-unmatched') || '0');
            
            new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Matched', 'Unmatched'],
                datasets: [{
                    data: [matched, unmatched],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        'rgba(34, 197, 94, 1)',
                        'rgba(245, 158, 11, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = matched + unmatched;
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        } catch (error) {
            console.error("Error initializing match rate chart:", error);
        }
    }
}

// Initialize DataTables
function initializeDataTables() {
    // Check if DataTable is defined
    if (typeof DataTable === 'undefined' && typeof $.fn.DataTable === 'undefined') {
        console.log('DataTables not loaded, skipping table initialization');
        return;
    }

    try {
        const tables = document.querySelectorAll('.datatable');
        tables.forEach(table => {
            if (table.classList.contains('datatable-initialized')) return;
            
            try {
                // Try using the standalone version first
                if (typeof DataTable !== 'undefined') {
                    new DataTable(table, {
                        pageLength: 10,
                        lengthMenu: [5, 10, 25, 50],
                        responsive: true,
                        dom: 'Bfrtip',
                        buttons: [
                            'copy', 'csv', 'excel', 'pdf', 'print'
                        ]
                    });
                } 
                // Fall back to jQuery version if standalone isn't available
                else if (typeof $.fn.DataTable !== 'undefined') {
                    $(table).DataTable({
                        pageLength: 10,
                        lengthMenu: [5, 10, 25, 50],
                        responsive: true,
                        dom: 'Bfrtip',
                        buttons: [
                            'copy', 'csv', 'excel', 'pdf', 'print'
                        ]
                    });
                }
                
                table.classList.add('datatable-initialized');
            } catch (tableError) {
                console.error("Error initializing DataTable for specific table:", tableError);
            }
        });
    } catch (error) {
        console.error("Error in DataTables initialization:", error);
    }
}

// Format currency values with proper currency symbol
function formatCurrency(amount, currency = 'GBP') {
    const formatter = new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: currency
    });
    
    return formatter.format(amount);
}

// Format dates in a human-readable format
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

// Format timestamps with date and time
function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Show confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: 5000
    });
    
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}
