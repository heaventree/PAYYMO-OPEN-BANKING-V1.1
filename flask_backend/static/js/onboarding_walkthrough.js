/**
 * Animated Onboarding Walkthrough
 * Interactive first-time user guide that walks through key features of the Open Banking module
 * Highlights important elements with tooltips and animated indicators
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const walkthrough = {
        enabled: true,
        autoStart: false, // Set to false to prevent auto-start - less intrusive
        steps: [
            {
                target: '.dashboard-header',
                title: 'Welcome to Open Banking',
                content: 'This dashboard helps you connect bank accounts and match transactions to invoices automatically.',
                position: 'bottom'
            },
            {
                target: '.bank-connection-card',
                title: 'Connect Your Bank',
                content: 'Start by connecting your bank account. We support over 2,400 banks across Europe.',
                position: 'right'
            },
            {
                target: '.transactions-table',
                title: 'Transaction Management',
                content: 'View all your transactions here. The system will automatically try to match them to invoices.',
                position: 'top'
            },
            {
                target: '.financial-goals',
                title: 'Financial Goals',
                content: 'Track your progress toward important financial targets.',
                position: 'left'
            },
            {
                target: '.quick-insights-widget',
                title: 'AI-Powered Insights',
                content: 'Get smart recommendations based on your transaction data and payment patterns.',
                position: 'left'
            }
        ],
        completionCallback: () => {
            // Save to localStorage that walkthrough is completed
            localStorage.setItem('walkthroughCompleted', 'true');
            showToast('Walkthrough completed! You can restart it anytime from the help menu.', 'success');
        }
    };

    let currentStep = 0;
    let walkthroughActive = false;
    let walkthroughPopover = null;
    let highlightOverlay = null;

    // Initialize highlight overlay
    function createHighlightOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'walkthrough-overlay';
        document.body.appendChild(overlay);
        return overlay;
    }

    // Create and show popover for the current step
    function showCurrentStep() {
        if (currentStep >= walkthrough.steps.length) {
            endWalkthrough(true);
            return;
        }

        const step = walkthrough.steps[currentStep];
        const targetElement = document.querySelector(step.target);
        
        if (!targetElement) {
            console.warn(`Target element ${step.target} not found, skipping step`);
            currentStep++;
            showCurrentStep();
            return;
        }

        // Position the highlight
        positionHighlight(targetElement);
        
        // Create popover if it doesn't exist
        if (!walkthroughPopover) {
            walkthroughPopover = document.createElement('div');
            walkthroughPopover.className = 'walkthrough-popover animate__animated animate__fadeIn';
            document.body.appendChild(walkthroughPopover);
        }

        // Populate and position popover
        walkthroughPopover.innerHTML = `
            <div class="walkthrough-header">
                <h5>${step.title}</h5>
                <button type="button" class="btn-close walkthrough-close" aria-label="Close walkthrough"></button>
            </div>
            <div class="walkthrough-body">
                <p>${step.content}</p>
            </div>
            <div class="walkthrough-footer">
                <div class="walkthrough-progress">
                    <span>${currentStep + 1}/${walkthrough.steps.length}</span>
                </div>
                <div class="walkthrough-buttons">
                    <button class="btn btn-sm btn-danger walkthrough-close me-2">Exit Tour</button>
                    ${currentStep > 0 ? '<button class="btn btn-sm btn-secondary walkthrough-prev">Previous</button>' : ''}
                    <button class="btn btn-sm btn-primary walkthrough-next">${currentStep < walkthrough.steps.length - 1 ? 'Next' : 'Finish'}</button>
                </div>
            </div>
        `;

        // Position the popover relative to the target element
        positionPopover(targetElement, step.position);

        // Add event listeners to all close buttons
        const closeButtons = walkthroughPopover.querySelectorAll('.walkthrough-close');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => endWalkthrough(false));
        });
        
        const nextBtn = walkthroughPopover.querySelector('.walkthrough-next');
        if (nextBtn) {
            nextBtn.addEventListener('click', nextStep);
        }
        
        const prevBtn = walkthroughPopover.querySelector('.walkthrough-prev');
        if (prevBtn) {
            prevBtn.addEventListener('click', prevStep);
        }

        // Add pulse animation to target
        targetElement.classList.add('walkthrough-target-pulse');
    }

    // Position the highlight overlay around the target element
    function positionHighlight(targetElement) {
        if (!highlightOverlay) return;
        
        // Scroll element into view with some padding at the top
        const scrollPadding = 100; // Pixels from top of viewport
        const elementTop = targetElement.getBoundingClientRect().top + window.scrollY;
        const targetScrollPosition = elementTop - scrollPadding;
        
        // Smooth scroll to the element
        window.scrollTo({
            top: targetScrollPosition,
            behavior: 'smooth'
        });
        
        // After scrolling, position the highlight
        setTimeout(() => {
            const rect = targetElement.getBoundingClientRect();
            const padding = 10; // Extra space around the element
            
            highlightOverlay.style.display = 'block';
            highlightOverlay.innerHTML = `
                <div class="walkthrough-mask"></div>
                <div class="walkthrough-highlight" style="
                    top: ${rect.top - padding + window.scrollY}px;
                    left: ${rect.left - padding + window.scrollX}px;
                    width: ${rect.width + padding * 2}px;
                    height: ${rect.height + padding * 2}px;
                    border-radius: 8px;
                "></div>
            `;
        }, 300); // Small delay to allow the scroll to complete
    }

    // Position the popover relative to the target element
    function positionPopover(targetElement, position = 'bottom') {
        if (!walkthroughPopover) return;
        
        // Position popover after a slight delay to ensure accurate positioning after any scrolling
        setTimeout(() => {
            const targetRect = targetElement.getBoundingClientRect();
            const popoverRect = walkthroughPopover.getBoundingClientRect();
            const padding = 20; // Distance from target
            const viewportPadding = 15; // Minimum distance from viewport edges
            
            let top, left;
            let originalPosition = position;
    
            // Determine the best position based on available space
            // If the target is close to the top of the viewport, prefer bottom position
            if (targetRect.top < 200 && position === 'top') {
                position = 'bottom';
            }
            
            // If the target is close to the bottom of the viewport, prefer top position
            if (targetRect.bottom > window.innerHeight - 200 && position === 'bottom') {
                position = 'top';
            }
            
            // If the target is close to the left edge, prefer right position
            if (targetRect.left < 250 && position === 'left') {
                position = 'right';
            }
            
            // If the target is close to the right edge, prefer left position
            if (targetRect.right > window.innerWidth - 250 && position === 'right') {
                position = 'left';
            }
    
            switch (position) {
                case 'top':
                    top = targetRect.top - popoverRect.height - padding + window.scrollY;
                    left = targetRect.left + (targetRect.width / 2) - (popoverRect.width / 2) + window.scrollX;
                    break;
                case 'bottom':
                    top = targetRect.bottom + padding + window.scrollY;
                    left = targetRect.left + (targetRect.width / 2) - (popoverRect.width / 2) + window.scrollX;
                    break;
                case 'left':
                    top = targetRect.top + (targetRect.height / 2) - (popoverRect.height / 2) + window.scrollY;
                    left = targetRect.left - popoverRect.width - padding + window.scrollX;
                    break;
                case 'right':
                    top = targetRect.top + (targetRect.height / 2) - (popoverRect.height / 2) + window.scrollY;
                    left = targetRect.right + padding + window.scrollX;
                    break;
                default:
                    top = targetRect.bottom + padding + window.scrollY;
                    left = targetRect.left + window.scrollX;
            }
    
            // Make sure popover stays within viewport
            if (left < viewportPadding) left = viewportPadding;
            if (left + popoverRect.width > window.innerWidth - viewportPadding) {
                left = window.innerWidth - popoverRect.width - viewportPadding;
            }
            
            // Ensure the popover is not too close to the top of the viewport
            const topViewportDistance = top - window.scrollY;
            if (topViewportDistance < viewportPadding) {
                top = window.scrollY + viewportPadding;
            }
            
            // Ensure the popover is visible if it would appear below the viewport
            const bottomViewportDistance = (top + popoverRect.height) - (window.scrollY + window.innerHeight);
            if (bottomViewportDistance > -viewportPadding) {
                top = window.scrollY + window.innerHeight - popoverRect.height - viewportPadding;
            }
            
            walkthroughPopover.style.top = `${top}px`;
            walkthroughPopover.style.left = `${left}px`;
    
            // Add position-specific class for styling arrow
            walkthroughPopover.className = walkthroughPopover.className
                .replace(/ position-(top|bottom|left|right)/g, '')
                + ` position-${position}`;
        }, 350); // Delay slightly longer than the highlight positioning to ensure accurate placement
    }

    // Go to next step
    function nextStep() {
        // Remove pulse from current target
        const currentTarget = document.querySelector(walkthrough.steps[currentStep].target);
        if (currentTarget) {
            currentTarget.classList.remove('walkthrough-target-pulse');
        }
        
        currentStep++;
        showCurrentStep();
    }

    // Go to previous step
    function prevStep() {
        // Remove pulse from current target
        const currentTarget = document.querySelector(walkthrough.steps[currentStep].target);
        if (currentTarget) {
            currentTarget.classList.remove('walkthrough-target-pulse');
        }
        
        currentStep--;
        if (currentStep < 0) currentStep = 0;
        showCurrentStep();
    }

    // Start the walkthrough
    function startWalkthrough() {
        if (walkthroughActive) return;
        walkthroughActive = true;
        currentStep = 0;
        
        // Create overlay if it doesn't exist
        if (!highlightOverlay) {
            highlightOverlay = createHighlightOverlay();
        }
        
        // Show first step
        showCurrentStep();
    }

    // End the walkthrough
    function endWalkthrough(completed = false) {
        walkthroughActive = false;
        
        // Remove highlight from current target
        const currentTarget = document.querySelector(walkthrough.steps[currentStep]?.target);
        if (currentTarget) {
            currentTarget.classList.remove('walkthrough-target-pulse');
        }
        
        // Remove popover with animation
        if (walkthroughPopover) {
            walkthroughPopover.classList.add('animate__fadeOut');
            setTimeout(() => {
                if (walkthroughPopover) {
                    walkthroughPopover.remove();
                    walkthroughPopover = null;
                }
            }, 300);
        }
        
        // Remove overlay
        if (highlightOverlay) {
            highlightOverlay.style.display = 'none';
        }
        
        // Call completion callback if walkthrough was completed
        if (completed && typeof walkthrough.completionCallback === 'function') {
            walkthrough.completionCallback();
        }
    }

    // Add walkthrough button to the page
    function addWalkthroughButton() {
        const helpMenu = document.querySelector('.help-menu');
        if (!helpMenu) return;
        
        const walkthroughButton = document.createElement('button');
        walkthroughButton.className = 'dropdown-item';
        walkthroughButton.innerHTML = '<i class="fas fa-route me-2"></i> Start Guided Tour';
        walkthroughButton.addEventListener('click', startWalkthrough);
        
        helpMenu.appendChild(walkthroughButton);
    }

    // Check if we should auto-start the walkthrough
    function checkAutoStartWalkthrough() {
        // Only auto-start if specifically enabled AND for first-time users
        if (walkthrough.enabled && walkthrough.autoStart && !localStorage.getItem('walkthroughCompleted')) {
            // Add a small dismiss button to the corner of the screen first
            const dismissButton = document.createElement('button');
            dismissButton.className = 'walkthrough-dismiss-btn btn btn-sm btn-danger position-fixed';
            dismissButton.innerHTML = 'Skip Tour';
            dismissButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 9999; border-radius: 20px; opacity: 0.8;';
            document.body.appendChild(dismissButton);
            
            dismissButton.addEventListener('click', () => {
                dismissButton.remove();
                localStorage.setItem('walkthroughCompleted', 'true');
            });
            
            // Delay start to ensure page is fully loaded
            const tourTimeout = setTimeout(startWalkthrough, 1500);
            
            // Allow quick dismissal
            dismissButton.addEventListener('click', () => {
                clearTimeout(tourTimeout);
                dismissButton.remove();
            });
        }
        
        // Always add the button to manually start the walkthrough
        addWalkthroughButton();
    }

    // Initialize
    checkAutoStartWalkthrough();

    // Expose functions for external use
    window.onboardingWalkthrough = {
        start: startWalkthrough,
        end: endWalkthrough
    };
});