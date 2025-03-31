/**
 * Stripe Connection Wizard
 * This script controls the Stripe connection wizard modal and steps
 */
document.addEventListener("DOMContentLoaded", function() {
    console.log("Stripe wizard script loaded");
    
    // Check if the modal element exists
    const stripeModal = document.getElementById('stripeConnectionModal');
    if (!stripeModal) {
        console.log("Stripe connection modal not found");
        return;
    }
    
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
        
        // Update progress bar
        const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
        progressBar.style.width = `${progressPercentage}%`;
        progressBar.setAttribute('aria-valuenow', progressPercentage);
    }
    
    // Show the current step
    function showCurrentStep() {
        stepContents.forEach((content, index) => {
            if (index + 1 === currentStep) {
                content.classList.remove('d-none');
            } else {
                content.classList.add('d-none');
            }
        });
        
        // Update the next button text based on the current step
        if (currentStep === totalSteps) {
            nextButton.textContent = "Complete";
        } else if (currentStep === 1) {
            nextButton.textContent = "Continue to Authorization";
        } else {
            nextButton.textContent = "Continue";
        }
    }
    
    // Handle the next button click
    nextButton.addEventListener('click', function() {
        if (currentStep < totalSteps) {
            // Move to the next step
            currentStep++;
            updateStepIcons();
            showCurrentStep();
            
            // If we're in step 2, we would redirect to Stripe in a real implementation
            if (currentStep === 2) {
                // Simulate a Stripe redirect with a delay in this demo
                setTimeout(() => {
                    // In a real implementation, this would be a redirection to Stripe's OAuth page
                    // For demo purposes, we'll simulate a successful authorization
                    currentStep++;
                    updateStepIcons();
                    showCurrentStep();
                    
                    // Update the Stripe account email in the completion step
                    const stripeAccountEmail = document.getElementById('stripeAccountEmail');
                    if (stripeAccountEmail) {
                        stripeAccountEmail.textContent = 'demo@example.com';
                    }
                    
                    // Update the footer button
                    stripeModal.querySelector('.modal-footer').innerHTML = `
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
                    `;
                }, 1000);
            }
        } else {
            // Handle completion (step 3)
            stripeModal.querySelector('.modal-footer').innerHTML = `
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
            `;
        }
    });
    
    // Reset wizard when modal is hidden
    stripeModal.addEventListener('hidden.bs.modal', function() {
        resetWizard();
    });
    
    // Reset the wizard state
    function resetWizard() {
        currentStep = 1;
        
        // Reset the UI
        updateStepIcons();
        showCurrentStep();
        
        // Reset the modal footer
        stripeModal.querySelector('.modal-footer').innerHTML = `
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="stripeWizardNextBtn">Continue to Authorization</button>
        `;
        
        // Re-attach event listener to the new button
        document.getElementById('stripeWizardNextBtn').addEventListener('click', function() {
            if (currentStep < totalSteps) {
                currentStep++;
                updateStepIcons();
                showCurrentStep();
                
                // Handle the simulated Stripe OAuth redirect
                if (currentStep === 2) {
                    setTimeout(() => {
                        currentStep++;
                        updateStepIcons();
                        showCurrentStep();
                        
                        const stripeAccountEmail = document.getElementById('stripeAccountEmail');
                        if (stripeAccountEmail) {
                            stripeAccountEmail.textContent = 'demo@example.com';
                        }
                        
                        stripeModal.querySelector('.modal-footer').innerHTML = `
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
                        `;
                    }, 1000);
                }
            } else {
                stripeModal.querySelector('.modal-footer').innerHTML = `
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
                `;
            }
        });
    }
    
    // Initialize Lucide icons if they're available
    if (window.lucide) {
        lucide.createIcons();
    }
    
    // Initialize the wizard
    updateStepIcons();
    showCurrentStep();
});