/**
 * Stripe Connection Wizard
 * This script controls the Stripe connection wizard modal and steps
 */
document.addEventListener("DOMContentLoaded", function() {
    console.log("Stripe wizard script loaded");
    
    // Check if the modal element exists
    const stripeModal = document.getElementById('stripeConnectionModal');
    if (!stripeModal) return;
    
    // Initialize the wizard
    console.log("Initializing Stripe connection wizard");
    
    // Elements
    const steps = stripeModal.querySelectorAll('.step');
    const stepContents = stripeModal.querySelectorAll('.step-content');
    const nextButton = document.getElementById('stripeWizardNextBtn');
    const progressBar = stripeModal.querySelector('.progress-bar');
    
    console.log(`Found ${steps.length} steps and ${stepContents.length} step contents`);
    
    let currentStep = 1;
    const totalSteps = steps.length;
    
    // Update the current step display and progress bar
    function updateStepIcons() {
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            const stepIcon = step.querySelector('.step-icon');
            
            if (stepNumber < currentStep) {
                // Completed step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-purple', 'text-white');
                stepIcon.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i>';
            } else if (stepNumber === currentStep) {
                // Current step
                stepIcon.classList.remove('bg-light', 'border');
                stepIcon.classList.add('bg-purple', 'text-white');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
            } else {
                // Upcoming step
                stepIcon.classList.remove('bg-purple', 'text-white');
                stepIcon.classList.add('bg-light', 'border');
                stepIcon.innerHTML = `<span>${stepNumber}</span>`;
            }
        });
        
        // Update progress bar
        const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        
        // Update Feather icons
        if (window.feather) {
            feather.replace();
        }
    }
    
    // Reset the wizard to the first step
    function resetWizard() {
        currentStep = 1;
        updateStepIcons();
        
        // Hide all step contents except the first one
        stepContents.forEach((content, index) => {
            if (index === 0) {
                content.classList.remove('d-none');
            } else {
                content.classList.add('d-none');
            }
        });
        
        // Update the next button text
        nextButton.textContent = 'Continue';
        nextButton.classList.remove('btn-success');
        nextButton.classList.add('btn-purple');
        nextButton.disabled = false;
    }
    
    // Handle next button click
    if (nextButton) {
        console.log("Adding event listener to next button");
        nextButton.addEventListener('click', function() {
            if (currentStep === totalSteps) {
                // Last step - close the modal
                const modalInstance = bootstrap.Modal.getInstance(stripeModal);
                modalInstance.hide();
                resetWizard();
                return;
            }
            
            if (currentStep === 1) {
                // First step - continue to authorization
                // In a real app, we would validate input here
                
                // Move to the next step
                stepContents[currentStep - 1].classList.add('d-none');
                currentStep++;
                stepContents[currentStep - 1].classList.remove('d-none');
                
                // Update button text
                nextButton.textContent = 'Authorize with Stripe';
                
            } else if (currentStep === 2) {
                // Second step - authorization with Stripe
                // In a real app, we would redirect to Stripe OAuth here
                // For demo purposes, we'll simulate a successful authorization
                
                // Show loading state
                nextButton.disabled = true;
                nextButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Authorizing...';
                
                // Simulate API call delay
                setTimeout(function() {
                    // Move to the next step
                    stepContents[currentStep - 1].classList.add('d-none');
                    currentStep++;
                    stepContents[currentStep - 1].classList.remove('d-none');
                    
                    // Update button
                    nextButton.disabled = false;
                    nextButton.textContent = 'Finish';
                    nextButton.classList.remove('btn-purple');
                    nextButton.classList.add('btn-success');
                    
                    updateStepIcons();
                }, 1500);
            }
            
            updateStepIcons();
        });
    }
    
    // Reset wizard when modal is hidden
    stripeModal.addEventListener('hidden.bs.modal', resetWizard);
    
    // Initialize the wizard
    resetWizard();
    console.log("Stripe connection wizard initialization complete");
});