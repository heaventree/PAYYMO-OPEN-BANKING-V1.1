/**
 * AI-Powered Financial Insights Widget
 * Self-contained module for displaying AI-driven financial insights
 * Analyzes transaction patterns and provides smart recommendations
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Quick Insights Widget');
    
    // Wait a moment for all elements to be fully loaded and rendered
    setTimeout(function() {
        initializeWidget();
    }, 500);
});

function initializeWidget() {
    // Find the widget container
    let widget = document.getElementById('quick-insights-widget');
    
    if (!widget) {
        console.warn('Quick Insights Widget element not found');
        // Try again in a second - the DOM might still be loading
        setTimeout(function() {
            initializeWidget();
        }, 1000);
        return;
    }
    
    console.log('Quick Insights Widget found and initializing')
    
    // Widget state
    let currentInsightIndex = 0;
    let insights = [];
    
    // Sample insights data (would normally come from the server)
    const sampleInsights = [
        {
            title: 'Improve Cash Flow',
            content: 'Based on your transaction history, setting up automatic invoice reminders could improve payment times by up to 30%.',
            icon: 'trending-up',
            type: 'success'
        },
        {
            title: 'Potential Duplicate Payment',
            content: 'We detected similar transactions on Mar 15 and Mar 17 to the same vendor. You might want to check for duplicates.',
            icon: 'alert-triangle',
            type: 'warning'
        },
        {
            title: 'Banking Connection',
            content: 'Connect another bank account to get a more complete picture of your finances.',
            icon: 'link',
            type: 'info'
        }
    ];
    
    // Initialize the widget
    function initialize() {
        // Add event listeners to controls
        widget.querySelector('.minimize-btn')?.addEventListener('click', toggleMinimize);
        widget.querySelector('.close-btn')?.addEventListener('click', hideWidget);
        widget.querySelector('.prev-btn')?.addEventListener('click', showPrevInsight);
        widget.querySelector('.next-btn')?.addEventListener('click', showNextInsight);
        widget.querySelector('.refresh-btn')?.addEventListener('click', refreshInsight);
        
        // Make the widget draggable
        makeDraggable();
        
        // Load insights data
        loadInsightsFromServer();
    }
    
    // Display a specific insight
    function showInsight(index) {
        if (insights.length === 0) return;
        
        // Ensure index is within bounds
        if (index < 0) index = insights.length - 1;
        if (index >= insights.length) index = 0;
        
        currentInsightIndex = index;
        
        const insight = insights[currentInsightIndex];
        const contentArea = widget.querySelector('.insights-content');
        if (!contentArea) return;
        
        // Update content
        const titleElement = contentArea.querySelector('.insight-title');
        const contentElement = contentArea.querySelector('.insight-content');
        const iconElement = contentArea.querySelector('.insight-icon');
        
        if (titleElement) titleElement.textContent = insight.title;
        if (contentElement) contentElement.textContent = insight.content;
        
        // Update icon
        if (iconElement) {
            // Clear previous icon classes
            iconElement.className = 'insight-icon';
            // Add new icon class
            iconElement.classList.add(`text-${insight.type}`);
            // Update icon data attribute
            iconElement.setAttribute('data-lucide', insight.icon);
            // Refresh the icon
            lucide.createIcons({
                icons: {
                    [insight.icon]: iconElement
                }
            });
        }
        
        // Update pagination indicator
        const paginationElement = widget.querySelector('.pagination-indicator');
        if (paginationElement) {
            paginationElement.textContent = `${currentInsightIndex + 1}/${insights.length}`;
        }
    }
    
    // Show next insight
    function showNextInsight() {
        showInsight(currentInsightIndex + 1);
    }
    
    // Show previous insight
    function showPrevInsight() {
        showInsight(currentInsightIndex - 1);
    }
    
    // Refresh insights data
    function refreshInsight() {
        // Simulated refresh animation
        const refreshBtn = widget.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.classList.add('animate__animated', 'animate__rotateIn');
            setTimeout(() => {
                refreshBtn.classList.remove('animate__animated', 'animate__rotateIn');
                loadInsightsFromServer();
            }, 500);
        }
    }
    
    // Toggle minimize state
    function toggleMinimize() {
        widget.classList.toggle('widget-minimized');
        
        // Update button icon
        const minimizeBtn = widget.querySelector('.minimize-btn');
        if (minimizeBtn) {
            const isMinimized = widget.classList.contains('widget-minimized');
            minimizeBtn.setAttribute('data-lucide', isMinimized ? 'maximize-2' : 'minimize-2');
            lucide.createIcons();
        }
        
        // Store state in localStorage
        localStorage.setItem('insightsWidgetMinimized', widget.classList.contains('widget-minimized'));
    }
    
    // Hide widget
    function hideWidget() {
        widget.style.display = 'none';
        localStorage.setItem('insightsWidgetHidden', 'true');
    }
    
    // Show widget
    function showWidget() {
        widget.style.display = 'block';
        localStorage.setItem('insightsWidgetHidden', 'false');
    }
    
    // Load insights from server
    function loadInsightsFromServer() {
        // In a real implementation, this would be an AJAX call to the server
        // For now, we'll use the sample data with a simulated delay
        const loadingIndicator = widget.querySelector('.loading-indicator');
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        
        setTimeout(() => {
            insights = sampleInsights;
            showInsight(0);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }, 500);
    }
    
    // Make the widget draggable
    function makeDraggable() {
        const header = widget.querySelector('.card-header');
        if (!header) return;
        
        let isDragging = false;
        let offsetX, offsetY;
        
        header.addEventListener('mousedown', startDrag);
        
        function startDrag(e) {
            isDragging = true;
            
            // Get the current position of the widget
            const rect = widget.getBoundingClientRect();
            
            // Calculate the offset from the pointer to the widget's top-left corner
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            
            // Add event listeners for dragging and releasing
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
            
            // Prevent text selection during drag
            header.style.userSelect = 'none';
        }
        
        function drag(e) {
            if (!isDragging) return;
            
            // Calculate new position
            const x = e.clientX - offsetX;
            const y = e.clientY - offsetY;
            
            // Set new position
            widget.style.left = x + 'px';
            widget.style.top = y + 'px';
            
            // Make sure the widget stays fixed
            widget.style.position = 'fixed';
        }
        
        function stopDrag() {
            isDragging = false;
            
            // Remove event listeners
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
            
            // Restore text selection
            header.style.userSelect = '';
            
            // Store position in localStorage
            localStorage.setItem('insightsWidgetPosition', JSON.stringify({
                left: widget.style.left,
                top: widget.style.top
            }));
        }
    }
    
    // Initialize
    initialize();
}