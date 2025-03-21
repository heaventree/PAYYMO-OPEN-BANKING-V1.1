/**
 * Bank Connection Wizard
 * This script controls the bank connection wizard modal and steps
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Bank wizard script loaded');
    // Get elements
    const bankConnectionModal = document.getElementById('bankConnectionModal');
    
    if (!bankConnectionModal) {
        console.log('Bank connection modal not found');
        return;
    }
    
    console.log('Initializing bank connection wizard');
    const nextButton = document.getElementById('bankWizardNextBtn');
    const progressBar = bankConnectionModal.querySelector('.progress-bar');
    const steps = bankConnectionModal.querySelectorAll('.step');
    const stepContents = bankConnectionModal.querySelectorAll('.step-content');
    
    let currentStep = 1;
    const totalSteps = steps.length;
    
    console.log(`Found ${steps.length} steps and ${stepContents.length} step contents`);
    
    // Initialize bank options
    const bankOptions = bankConnectionModal.querySelectorAll('.bank-option');
    console.log(`Found ${bankOptions.length} bank options`);
    
    // Handle bank selection
    bankOptions.forEach(option => {
        option.addEventListener('click', function() {
            console.log('Bank option clicked');
            // Remove selection from all options
            bankOptions.forEach(opt => opt.classList.remove('border-primary'));
            
            // Add selection to clicked option
            this.classList.add('border-primary');
            
            // Enable next button if disabled
            if (nextButton) {
                nextButton.disabled = false;
                console.log('Next button enabled');
            }
            
            // Update bank name in the authorization step
            const bankName = this.querySelector('h6').textContent;
            const authorizeHeader = bankConnectionModal.querySelector('.step-2 h5');
            if (authorizeHeader) {
                authorizeHeader.textContent = `Connect to ${bankName}`;
                console.log(`Updated header to: Connect to ${bankName}`);
            }
        });
    });
    
    // Handle next button click
    if (nextButton) {
        console.log('Adding event listener to next button');
        nextButton.addEventListener('click', function(e) {
            console.log('Next button clicked, current step:', currentStep);
            if (currentStep < totalSteps) {
                // Update button text based on step
                if (currentStep === 1) {
                    this.textContent = 'Continue to Bank';
                    console.log('Updated button text: Continue to Bank');
                } else if (currentStep === 2) {
                    this.textContent = 'Done';
                    console.log('Updated button text: Done');
                }
                
                // Hide current step content
                stepContents[currentStep - 1].classList.add('d-none');
                console.log(`Hiding step ${currentStep} content`);
                
                // Show next step content
                currentStep++;
                stepContents[currentStep - 1].classList.remove('d-none');
                console.log(`Showing step ${currentStep} content`);
                
                // Update progress bar
                const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
                progressBar.style.width = `${progress}%`;
                progressBar.setAttribute('aria-valuenow', progress);
                console.log(`Updated progress bar to ${progress}%`);
                
                // Update step icons
                updateStepIcons();
                
                // If we're at the last step, simulate completion
                if (currentStep === totalSteps) {
                    this.dataset.bsDismiss = 'modal';
                    console.log('At last step, adding dismiss attribute');
                }
            } else {
                // Reset to first step for demo purposes
                resetWizard();
                console.log('Resetting wizard');
            }
        });
    } else {
        console.error('Next button not found in the bank connection wizard');
    }
    
    // Handle modal hidden event to reset wizard
    bankConnectionModal.addEventListener('hidden.bs.modal', function() {
        console.log('Modal hidden, resetting wizard');
        resetWizard();
    });
    
    // Function to update step icons
    function updateStepIcons() {
        console.log('Updating step icons');
        steps.forEach((step, index) => {
            const stepIcon = step.querySelector('.step-icon');
            const stepNumber = index + 1;
            
            if (stepNumber < currentStep) {
                // Completed step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-primary', 'text-white');
                stepIcon.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i>';
                console.log(`Step ${stepNumber} marked as completed`);
            } else if (stepNumber === currentStep) {
                // Current step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-primary', 'text-white');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
                console.log(`Step ${stepNumber} marked as current`);
            } else {
                // Future step
                stepIcon.classList.remove('bg-primary', 'text-white');
                stepIcon.classList.add('bg-light', 'border');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
                console.log(`Step ${stepNumber} marked as future`);
            }
        });
        
        // Reinitialize Lucide icons
        if (window.lucide) {
            console.log('Reinitializing Lucide icons');
            lucide.createIcons();
        } else {
            console.warn('Lucide not available');
        }
    }
    
    // Function to reset wizard
    function resetWizard() {
        console.log('Resetting wizard to initial state');
        currentStep = 1;
        
        // Reset progress bar
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        
        // Reset step contents visibility
        stepContents.forEach((content, index) => {
            if (index === 0) {
                content.classList.remove('d-none');
            } else {
                content.classList.add('d-none');
            }
        });
        
        // Reset step icons
        steps.forEach((step, index) => {
            const stepIcon = step.querySelector('.step-icon');
            const stepNumber = index + 1;
            
            stepIcon.classList.remove('bg-primary', 'text-white');
            stepIcon.classList.add('bg-light', 'border');
            
            if (stepNumber === 1) {
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-primary', 'text-white');
            }
            
            stepIcon.innerHTML = `<span>${stepNumber}</span>`;
        });
        
        // Reset button text
        if (nextButton) {
            nextButton.textContent = 'Continue to Authorization';
            nextButton.disabled = true;
            nextButton.removeAttribute('data-bs-dismiss');
        }
        
        // Reset bank selection
        bankOptions.forEach(option => {
            option.classList.remove('border-primary');
        });
    }
    
    // Initialize the wizard
    console.log('Bank connection wizard initialization complete');
});