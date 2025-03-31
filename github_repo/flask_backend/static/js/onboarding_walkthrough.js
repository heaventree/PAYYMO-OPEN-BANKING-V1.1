/**
 * Animated Onboarding Walkthrough
 * Interactive first-time user guide that walks through key features of the Open Banking module
 * Highlights important elements with tooltips and animated indicators
 */
document.addEventListener('DOMContentLoaded', function() {
    // Walkthrough configuration
    const walkthroughSteps = [
        {
            target: '.navbar-brand',
            title: 'Welcome to Payymo',
            content: 'This dashboard allows you to manage your financial transactions, connections, and invoice matches.',
            position: 'bottom'
        },
        {
            target: '.card:first-child',
            title: 'Dashboard Overview',
            content: 'Your dashboard provides a quick overview of your financial status and recent activities.',
            position: 'top'
        },
        {
            target: '.col-xl-3:nth-child(1)',
            title: 'Transaction Monitoring',
            content: 'Keep track of all your banking transactions in one place.',
            position: 'bottom'
        },
        {
            target: '.col-xl-3:nth-child(3)',
            title: 'Invoice Matching',
            content: 'We automatically match bank transactions to invoices for easier reconciliation.',
            position: 'bottom'
        },
        {
            target: '.btn-primary:first-of-type',
            title: 'Connect Your Bank',
            content: 'Start by connecting your bank account to import transactions.',
            position: 'right'
        },
        {
            target: '.btn-secondary:first-of-type',
            title: 'Stripe Integration',
            content: 'Connect your Stripe account to synchronize payment data.',
            position: 'right'
        }
    ];
    
    // State
    let currentStep = 0;
    let isWalkthroughActive = false;
    let highlightOverlay;
    let popover;
    
    // Create the highlight overlay element
    function createHighlightOverlay() {
        // Remove existing overlay if it exists
        if (highlightOverlay) {
            highlightOverlay.remove();
        }
        
        // Create new overlay
        highlightOverlay = document.createElement('div');
        highlightOverlay.className = 'walkthrough-overlay';
        highlightOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1049;
            pointer-events: none;
        `;
        
        document.body.appendChild(highlightOverlay);
        
        // Create popover container
        popover = document.createElement('div');
        popover.className = 'walkthrough-popover animate__animated animate__fadeIn';
        popover.style.cssText = `
            position: absolute;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            padding: 15px;
            width: 300px;
            z-index: 1050;
            pointer-events: auto;
        `;
        
        // Add controls
        popover.innerHTML = `
            <div class="walkthrough-header">
                <h5 class="walkthrough-title"></h5>
                <button type="button" class="btn-close" onclick="endWalkthrough()"></button>
            </div>
            <div class="walkthrough-body mt-2">
                <p class="walkthrough-content"></p>
            </div>
            <div class="walkthrough-footer d-flex justify-content-between mt-3">
                <button class="btn btn-sm btn-outline-secondary prev-btn">Previous</button>
                <div class="step-indicator small text-muted"></div>
                <button class="btn btn-sm btn-primary next-btn">Next</button>
            </div>
        `;
        
        document.body.appendChild(popover);
        
        // Add event listeners
        popover.querySelector('.prev-btn').addEventListener('click', prevStep);
        popover.querySelector('.next-btn').addEventListener('click', nextStep);
        popover.querySelector('.btn-close').addEventListener('click', () => endWalkthrough());
        
        // Make the overlay close the walkthrough when clicked
        highlightOverlay.style.pointerEvents = 'auto';
        highlightOverlay.addEventListener('click', () => endWalkthrough());
        
        return highlightOverlay;
    }
    
    // Show the current step
    function showCurrentStep() {
        const step = walkthroughSteps[currentStep];
        
        // Find the target element
        const targetSelector = step.target;
        const targetElement = document.querySelector(targetSelector);
        
        if (!targetElement) {
            console.warn(`Walkthrough target not found: ${targetSelector}`);
            nextStep(); // Skip this step
            return;
        }
        
        // Update popover content
        popover.querySelector('.walkthrough-title').textContent = step.title;
        popover.querySelector('.walkthrough-content').textContent = step.content;
        popover.querySelector('.step-indicator').textContent = `${currentStep + 1}/${walkthroughSteps.length}`;
        
        // Update button states
        popover.querySelector('.prev-btn').disabled = currentStep === 0;
        
        const nextBtn = popover.querySelector('.next-btn');
        if (currentStep === walkthroughSteps.length - 1) {
            nextBtn.textContent = 'Finish';
        } else {
            nextBtn.textContent = 'Next';
        }
        
        // Position the highlight around the target element
        positionHighlight(targetElement);
        
        // Position the popover
        positionPopover(targetElement, step.position || 'bottom');
    }
    
    // Position the highlight around the target element
    function positionHighlight(targetElement) {
        // Get the element's position and dimensions
        const rect = targetElement.getBoundingClientRect();
        
        // Create a cutout in the overlay
        highlightOverlay.innerHTML = `
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <mask id="mask">
                        <rect width="100%" height="100%" fill="white"/>
                        <rect x="${rect.left}" y="${rect.top}" width="${rect.width}" height="${rect.height}" fill="black" rx="4"/>
                    </mask>
                </defs>
                <rect width="100%" height="100%" fill="rgba(0, 0, 0, 0.5)" mask="url(#mask)"/>
                <rect x="${rect.left - 4}" y="${rect.top - 4}" width="${rect.width + 8}" height="${rect.height + 8}" 
                    fill="none" stroke="#007bff" stroke-width="2" rx="6"/>
            </svg>
        `;
    }
    
    // Position the popover relative to the target element
    function positionPopover(targetElement, position = 'bottom') {
        const rect = targetElement.getBoundingClientRect();
        const popoverRect = popover.getBoundingClientRect();
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - popoverRect.height - 15;
                left = rect.left + (rect.width / 2) - (popoverRect.width / 2);
                break;
            case 'bottom':
                top = rect.bottom + 15;
                left = rect.left + (rect.width / 2) - (popoverRect.width / 2);
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (popoverRect.height / 2);
                left = rect.left - popoverRect.width - 15;
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - (popoverRect.height / 2);
                left = rect.right + 15;
                break;
        }
        
        // Ensure the popover stays within the viewport
        if (left < 15) left = 15;
        if (left + popoverRect.width > window.innerWidth - 15) {
            left = window.innerWidth - popoverRect.width - 15;
        }
        if (top < 15) top = 15;
        if (top + popoverRect.height > window.innerHeight - 15) {
            top = window.innerHeight - popoverRect.height - 15;
        }
        
        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
    }
    
    // Next step
    function nextStep() {
        if (currentStep < walkthroughSteps.length - 1) {
            currentStep++;
            showCurrentStep();
        } else {
            endWalkthrough(true); // Completed
        }
    }
    
    // Previous step
    function prevStep() {
        if (currentStep > 0) {
            currentStep--;
            showCurrentStep();
        }
    }
    
    // Start the walkthrough
    function startWalkthrough() {
        isWalkthroughActive = true;
        createHighlightOverlay();
        currentStep = 0;
        showCurrentStep();
        
        // Make the function available globally
        window.endWalkthrough = endWalkthrough;
    }
    
    // End the walkthrough
    function endWalkthrough(completed = false) {
        isWalkthroughActive = false;
        
        if (highlightOverlay) {
            highlightOverlay.remove();
            highlightOverlay = null;
        }
        
        if (popover) {
            popover.remove();
            popover = null;
        }
        
        if (completed) {
            // Mark as completed in localStorage to prevent auto showing
            localStorage.setItem('walkthroughCompleted', 'true');
            
            // Show completion toast
            if (typeof showToast === 'function') {
                showToast('Walkthrough completed! You can restart it anytime from the Help menu.', 'success');
            }
        }
        
        // Remove global function
        delete window.endWalkthrough;
    }
    
    // Add walkthrough button to the help menu
    function addWalkthroughButton() {
        const helpMenu = document.querySelector('.help-menu');
        if (!helpMenu) return;
        
        const walkthroughItem = document.createElement('li');
        walkthroughItem.innerHTML = `<button class="dropdown-item" type="button"><i class="fas fa-map-marked-alt me-2"></i> Start Walkthrough</button>`;
        walkthroughItem.querySelector('button').addEventListener('click', startWalkthrough);
        
        helpMenu.appendChild(walkthroughItem);
    }
    
    // Check if we should auto-start the walkthrough
    function checkAutoStartWalkthrough() {
        // Only auto-start if this is the first visit (based on localStorage)
        const walkthroughCompleted = localStorage.getItem('walkthroughCompleted') === 'true';
        
        if (!walkthroughCompleted && document.querySelector('.dashboard-page')) {
            // Wait a bit to let the page settle
            setTimeout(startWalkthrough, 1000);
        }
    }
    
    // Initialize
    addWalkthroughButton();
    checkAutoStartWalkthrough();
});