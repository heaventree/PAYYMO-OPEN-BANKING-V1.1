/**
 * Stripe Connection Wizard
 * This script controls the Stripe connection wizard modal and steps
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Stripe wizard script loaded');
    
    // Find the Stripe wizard modal
    const stripeModal = document.getElementById('stripe-connection-modal');
    if (!stripeModal) {
        console.log('Stripe connection modal not found');
        return;
    }
    
    // Get all steps
    const steps = Array.from(stripeModal.querySelectorAll('.wizard-step'));
    if (steps.length === 0) return;
    
    // Get control buttons
    const nextBtn = stripeModal.querySelector('.next-step');
    const prevBtn = stripeModal.querySelector('.prev-step');
    const submitBtn = stripeModal.querySelector('.submit-step');
    
    // Current step index
    let currentStepIndex = 0;
    
    // Show the current step
    function showStep(index) {
        // Hide all steps
        steps.forEach(step => step.classList.add('d-none'));
        
        // Show the current step
        steps[index].classList.remove('d-none');
        
        // Update buttons
        if (index === 0) {
            prevBtn.classList.add('d-none');
        } else {
            prevBtn.classList.remove('d-none');
        }
        
        if (index === steps.length - 1) {
            nextBtn.classList.add('d-none');
            submitBtn.classList.remove('d-none');
        } else {
            nextBtn.classList.remove('d-none');
            submitBtn.classList.add('d-none');
        }
        
        // Update step indicators
        updateStepIcons();
    }
    
    // Go to next step
    function nextStep() {
        if (currentStepIndex < steps.length - 1) {
            // Validate current step
            if (validateCurrentStep()) {
                currentStepIndex++;
                showStep(currentStepIndex);
            }
        }
    }
    
    // Go to previous step
    function prevStep() {
        if (currentStepIndex > 0) {
            currentStepIndex--;
            showStep(currentStepIndex);
        }
    }
    
    // Validate the current step
    function validateCurrentStep() {
        // Validation logic depends on the step
        switch(currentStepIndex) {
            case 0: // Account type selection
                const accountType = stripeModal.querySelector('input[name="account-type"]:checked');
                if (!accountType) {
                    alert('Please select an account type');
                    return false;
                }
                return true;
                
            case 1: // Integration purpose
                const integrationPurpose = stripeModal.querySelector('input[name="integration-purpose"]:checked');
                if (!integrationPurpose) {
                    alert('Please select an integration purpose');
                    return false;
                }
                return true;
                
            default:
                return true;
        }
    }
    
    // Update step indicator icons
    function updateStepIcons() {
        const stepIcons = stripeModal.querySelectorAll('.step-indicator');
        stepIcons.forEach((icon, index) => {
            // Remove all classes
            icon.classList.remove('active', 'completed');
            
            // Add appropriate class
            if (index < currentStepIndex) {
                icon.classList.add('completed');
            } else if (index === currentStepIndex) {
                icon.classList.add('active');
            }
        });
    }
    
    // Reset the wizard
    function resetWizard() {
        currentStepIndex = 0;
        
        // Reset form fields
        const accountTypeRadios = stripeModal.querySelectorAll('input[name="account-type"]');
        if (accountTypeRadios.length > 0) {
            accountTypeRadios.forEach(radio => radio.checked = false);
            accountTypeRadios[0].checked = true;
        }
        
        const purposeRadios = stripeModal.querySelectorAll('input[name="integration-purpose"]');
        if (purposeRadios.length > 0) {
            purposeRadios.forEach(radio => radio.checked = false);
            purposeRadios[0].checked = true;
        }
        
        // Show the first step
        showStep(0);
    }
    
    // Add event listeners to buttons
    if (nextBtn) nextBtn.addEventListener('click', nextStep);
    if (prevBtn) prevBtn.addEventListener('click', prevStep);
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            // Submit the form or make an AJAX call
            if (validateCurrentStep()) {
                // Show loading indicator
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Connecting...';
                submitBtn.disabled = true;
                
                // In a real implementation, this would redirect to Stripe OAuth
                // For now, we'll just simulate a successful connection
                setTimeout(() => {
                    // In practice, this would open a new window or redirect to Stripe
                    // Create a fake OAuth window
                    window.open("about:blank", "stripe_oauth", "width=600,height=700");
                    
                    // Hide the modal
                    const modal = bootstrap.Modal.getInstance(stripeModal);
                    modal.hide();
                    
                    // Show success message
                    if (typeof showToast === 'function') {
                        showToast('Redirecting to Stripe for authorization...', 'info');
                    }
                    
                    // Reset form for next use
                    setTimeout(resetWizard, 500);
                    
                    // Reset button state
                    submitBtn.innerHTML = 'Connect to Stripe';
                    submitBtn.disabled = false;
                }, 1000);
            }
        });
    }
    
    // Initialize the wizard when the modal is shown
    stripeModal.addEventListener('show.bs.modal', resetWizard);
});