/**
 * Bank Connection Wizard
 * This script controls the bank connection wizard modal and steps
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const bankConnectionModal = document.getElementById('bankConnectionModal');
    
    if (!bankConnectionModal) return;
    
    const nextButton = document.getElementById('bankWizardNextBtn');
    const progressBar = bankConnectionModal.querySelector('.progress-bar');
    const steps = bankConnectionModal.querySelectorAll('.step');
    const stepContents = bankConnectionModal.querySelectorAll('.step-content');
    
    let currentStep = 1;
    const totalSteps = steps.length;
    
    // Initialize bank options
    const bankOptions = bankConnectionModal.querySelectorAll('.bank-option');
    
    // Handle bank selection
    bankOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selection from all options
            bankOptions.forEach(opt => opt.classList.remove('border-primary'));
            
            // Add selection to clicked option
            this.classList.add('border-primary');
            
            // Enable next button if disabled
            nextButton.disabled = false;
            
            // Update bank name in the authorization step
            const bankName = this.querySelector('h6').textContent;
            const authorizeHeader = bankConnectionModal.querySelector('.step-2 h5');
            if (authorizeHeader) {
                authorizeHeader.textContent = `Connect to ${bankName}`;
            }
        });
    });
    
    // Handle next button click
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            if (currentStep < totalSteps) {
                // Update button text based on step
                if (currentStep === 1) {
                    this.textContent = 'Continue to Bank';
                } else if (currentStep === 2) {
                    this.textContent = 'Done';
                }
                
                // Hide current step content
                stepContents[currentStep - 1].classList.add('d-none');
                
                // Show next step content
                currentStep++;
                stepContents[currentStep - 1].classList.remove('d-none');
                
                // Update progress bar
                const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
                progressBar.style.width = `${progress}%`;
                progressBar.setAttribute('aria-valuenow', progress);
                
                // Update step icons
                updateStepIcons();
                
                // If we're at the last step, simulate completion
                if (currentStep === totalSteps) {
                    this.dataset.bsDismiss = 'modal';
                }
            } else {
                // Reset to first step for demo purposes
                resetWizard();
            }
        });
    }
    
    // Handle modal hidden event to reset wizard
    bankConnectionModal.addEventListener('hidden.bs.modal', function() {
        resetWizard();
    });
    
    // Function to update step icons
    function updateStepIcons() {
        steps.forEach((step, index) => {
            const stepIcon = step.querySelector('.step-icon');
            const stepNumber = index + 1;
            
            if (stepNumber < currentStep) {
                // Completed step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-primary', 'text-white');
                stepIcon.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i>';
            } else if (stepNumber === currentStep) {
                // Current step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-primary', 'text-white');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
            } else {
                // Future step
                stepIcon.classList.remove('bg-primary', 'text-white');
                stepIcon.classList.add('bg-light', 'border');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
            }
        });
        
        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    // Function to reset wizard
    function resetWizard() {
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
});