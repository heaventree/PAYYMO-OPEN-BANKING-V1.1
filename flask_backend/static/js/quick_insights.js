/**
 * AI-Powered Financial Insights Widget
 * Self-contained module for displaying AI-driven financial insights in a floating widget
 * Analyzes transaction patterns and provides smart recommendations
 * Can be easily repositioned and integrated into different layouts
 */

const QuickInsightsWidget = (function() {
    // Private variables
    let currentInsightIndex = 0;
    let widgetVisible = true;
    let widgetElement;
    let insightData = [
        {
            type: 'Tip',
            title: 'Reference Numbers',
            text: 'Transactions with clear reference numbers have a 92% higher chance of automatic matching. Always include invoice numbers in payment references.'
        },
        {
            type: 'Insight',
            title: 'Transaction Patterns',
            text: 'Most of your successfully matched transactions occur on Mondays and Tuesdays. Consider scheduling invoice reminders for Friday afternoons.'
        },
        {
            type: 'Alert',
            title: 'Bank Connection',
            text: 'Your NatWest connection will expire in 7 days. Renew your connection before then to avoid missing transaction data.'
        },
        {
            type: 'Tip',
            title: 'Matching Efficiency',
            text: 'Set up automatic payment application rules to handle recurring payments from the same customers with similar amounts.'
        },
        {
            type: 'Insight',
            title: 'Reconciliation Time',
            text: 'You\'ve reduced your average reconciliation time by 64% since implementing Open Banking connections.'
        }
    ];
    
    // Private methods
    function initialize() {
        console.log('Initializing Quick Insights Widget');
        widgetElement = document.getElementById('quickInsightsWidget');
        
        if (!widgetElement) {
            console.warn('Quick Insights Widget element not found');
            return;
        }
        
        // Set up event listeners
        document.getElementById('refreshInsight').addEventListener('click', refreshInsight);
        document.getElementById('minimizeInsight').addEventListener('click', toggleMinimize);
        document.getElementById('closeInsight').addEventListener('click', hideWidget);
        document.getElementById('nextInsight').addEventListener('click', showNextInsight);
        document.getElementById('prevInsight').addEventListener('click', showPrevInsight);
        
        // Make widget draggable
        makeDraggable();
        
        // Initialize insight count
        document.getElementById('totalInsights').textContent = insightData.length;
        
        // Show first insight
        showInsight(0);
        
        // Load insights from the server if available
        loadInsightsFromServer();
    }
    
    function showInsight(index) {
        if (index < 0) index = insightData.length - 1;
        if (index >= insightData.length) index = 0;
        
        currentInsightIndex = index;
        
        const insight = insightData[index];
        const typeElement = document.querySelector('#quickInsightsWidget .badge');
        const titleElement = document.getElementById('insightTitle');
        const textElement = document.getElementById('insightText');
        const currentElement = document.getElementById('currentInsight');
        
        // Update content with animation
        textElement.classList.add('insight-animation');
        
        typeElement.textContent = insight.type;
        titleElement.textContent = insight.title;
        textElement.textContent = insight.text;
        currentElement.textContent = index + 1;
        
        // Set appropriate badge color
        typeElement.className = 'badge rounded-pill me-2';
        if (insight.type === 'Tip') {
            typeElement.classList.add('bg-info');
        } else if (insight.type === 'Insight') {
            typeElement.classList.add('bg-primary');
        } else if (insight.type === 'Alert') {
            typeElement.classList.add('bg-warning');
        }
        
        // Remove animation class after animation completes
        setTimeout(() => {
            textElement.classList.remove('insight-animation');
        }, 1000);
    }
    
    function showNextInsight() {
        showInsight(currentInsightIndex + 1);
    }
    
    function showPrevInsight() {
        showInsight(currentInsightIndex - 1);
    }
    
    function refreshInsight() {
        // Add a spinning animation to the refresh button
        const refreshIcon = document.querySelector('#refreshInsight i');
        refreshIcon.style.animation = 'spinner 1s linear';
        
        // After animation, show a random insight
        setTimeout(() => {
            const randomIndex = Math.floor(Math.random() * insightData.length);
            showInsight(randomIndex);
            refreshIcon.style.animation = '';
        }, 1000);
    }
    
    function toggleMinimize() {
        widgetElement.classList.toggle('minimized');
        
        // Change the minimize icon to maximize when minimized
        const minimizeIcon = document.querySelector('#minimizeInsight i');
        if (widgetElement.classList.contains('minimized')) {
            minimizeIcon.setAttribute('data-lucide', 'maximize-2');
        } else {
            minimizeIcon.setAttribute('data-lucide', 'minus');
        }
        
        // Update the icon
        lucide.createIcons({
            attrs: {
                'stroke-width': 1.5
            },
            elements: [minimizeIcon.parentElement]
        });
    }
    
    function hideWidget() {
        widgetElement.style.display = 'none';
        widgetVisible = false;
        
        // Create a "show insights" button at the bottom right
        if (!document.getElementById('showInsightsBtn')) {
            const showBtn = document.createElement('button');
            showBtn.id = 'showInsightsBtn';
            showBtn.className = 'position-fixed ai-insights-btn';
            showBtn.style.bottom = '10px';
            showBtn.style.right = '10px';
            showBtn.style.zIndex = '1050';
            showBtn.innerHTML = '<i data-lucide="brain" style="width: 18px; height: 18px; margin-right: 5px;"></i> AI Insights';
            showBtn.addEventListener('click', showWidget);
            
            document.body.appendChild(showBtn);
            
            // Initialize the icon
            lucide.createIcons({
                attrs: {
                    'stroke-width': 1.5
                },
                elements: [showBtn]
            });
        } else {
            document.getElementById('showInsightsBtn').style.display = 'block';
        }
    }
    
    function showWidget() {
        widgetElement.style.display = 'block';
        widgetVisible = true;
        
        // Hide the "show insights" button
        const showBtn = document.getElementById('showInsightsBtn');
        if (showBtn) {
            showBtn.style.display = 'none';
        }
    }
    
    function loadInsightsFromServer() {
        // This function would normally fetch insights from the server
        // For now we'll use our static data, but this could be enhanced
        // to load dynamic insights based on user data
        console.log('Would fetch insights from server in production');
    }
    
    function makeDraggable() {
        let isDragging = false;
        let offsetX, offsetY;
        const header = widgetElement.querySelector('.widget-header');
        
        header.addEventListener('mousedown', startDrag);
        
        function startDrag(e) {
            isDragging = true;
            offsetX = e.clientX - widgetElement.getBoundingClientRect().left;
            offsetY = e.clientY - widgetElement.getBoundingClientRect().top;
            
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
        }
        
        function drag(e) {
            if (!isDragging) return;
            
            const x = e.clientX - offsetX;
            const y = e.clientY - offsetY;
            
            // Ensure widget stays within viewport
            const maxX = window.innerWidth - widgetElement.offsetWidth;
            const maxY = window.innerHeight - widgetElement.offsetHeight;
            
            widgetElement.style.left = `${Math.max(0, Math.min(x, maxX))}px`;
            widgetElement.style.right = 'auto';
            widgetElement.style.top = `${Math.max(0, Math.min(y, maxY))}px`;
            widgetElement.style.bottom = 'auto';
        }
        
        function stopDrag() {
            isDragging = false;
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
        }
    }
    
    // Return public API
    return {
        init: initialize,
        next: showNextInsight,
        prev: showPrevInsight,
        refresh: refreshInsight,
        toggle: toggleMinimize,
        hide: hideWidget,
        show: showWidget
    };
})();

// Initialize the widget when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure all elements are ready
    setTimeout(() => {
        QuickInsightsWidget.init();
    }, 500);
});