/**
 * Bank Connection Wizard
 * This script controls the bank connection wizard modal and steps
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Bank wizard script loaded');
    
    // Find the bank wizard modal
    const bankModal = document.getElementById('bank-connection-modal');
    if (!bankModal) {
        console.log('Bank connection modal not found');
        return;
    }
    
    // Get all steps
    const steps = Array.from(bankModal.querySelectorAll('.wizard-step'));
    if (steps.length === 0) return;
    
    // Get control buttons
    const nextBtn = bankModal.querySelector('.next-step');
    const prevBtn = bankModal.querySelector('.prev-step');
    const submitBtn = bankModal.querySelector('.submit-step');
    
    // Current step index
    let currentStepIndex = 0;
    
    // Bank data
    let selectedCountry = 'GB';
    let selectedBank = null;
    let availableBanks = [];
    
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
            case 0: // Country selection
                selectedCountry = bankModal.querySelector('select[name="country"]').value;
                if (!selectedCountry) {
                    alert('Please select a country');
                    return false;
                }
                // Fetch available banks for the selected country
                fetchAvailableBanks(selectedCountry);
                return true;
                
            case 1: // Bank selection
                const bankRadios = bankModal.querySelectorAll('input[name="bank"]:checked');
                if (bankRadios.length === 0) {
                    alert('Please select a bank');
                    return false;
                }
                selectedBank = bankRadios[0].value;
                return true;
                
            default:
                return true;
        }
    }
    
    // Update step indicator icons
    function updateStepIcons() {
        const stepIcons = bankModal.querySelectorAll('.step-indicator');
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
    
    // Fetch available banks for a country
    function fetchAvailableBanks(country = 'GB') {
        // Show loading indicator
        const bankList = bankModal.querySelector('.bank-list');
        if (bankList) {
            bankList.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Loading banks...</p></div>';
        }
        
        // In a real implementation, this would be an AJAX call to the server
        // For now, we'll use sample data with a simulated delay
        setTimeout(() => {
            // Sample data
            availableBanks = [
                { id: 'bank-001', name: 'Bank of Example', logo: 'bank1.png', country: 'GB' },
                { id: 'bank-002', name: 'Financial Trust', logo: 'bank2.png', country: 'GB' },
                { id: 'bank-003', name: 'Digital Banking Co', logo: 'bank3.png', country: 'GB' },
                { id: 'bank-004', name: 'Global Bank UK', logo: 'bank4.png', country: 'GB' },
                { id: 'bank-005', name: 'Metro Financial', logo: 'bank5.png', country: 'GB' }
            ];
            
            // Render the bank options
            renderBankOptions();
        }, 1000);
    }
    
    // Render the bank options
    function renderBankOptions() {
        const bankList = bankModal.querySelector('.bank-list');
        if (!bankList) return;
        
        // Filter banks by selected country
        const filteredBanks = availableBanks.filter(bank => bank.country === selectedCountry);
        
        if (filteredBanks.length === 0) {
            bankList.innerHTML = '<div class="alert alert-info">No banks available for the selected country.</div>';
            return;
        }
        
        // Create bank options HTML
        let html = '';
        filteredBanks.forEach(bank => {
            html += `
                <div class="bank-option card mb-2">
                    <div class="card-body">
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="bank" id="${bank.id}" value="${bank.id}">
                            <label class="form-check-label d-flex align-items-center" for="${bank.id}">
                                <div class="bank-logo me-3">
                                    <i data-lucide="building" style="width: 24px; height: 24px;"></i>
                                </div>
                                <div class="bank-info">
                                    <strong>${bank.name}</strong>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Add search box
        const searchBox = `
            <div class="mb-3">
                <input type="text" class="form-control bank-search" placeholder="Search for a bank...">
            </div>
        `;
        
        bankList.innerHTML = searchBox + html;
        
        // Initialize search functionality
        const searchInput = bankList.querySelector('.bank-search');
        if (searchInput) {
            searchInput.addEventListener('input', filterBanks);
        }
        
        // Initialize Lucide icons
        lucide.createIcons();
    }
    
    // Filter banks based on search input
    function filterBanks() {
        const searchInput = bankModal.querySelector('.bank-search');
        if (!searchInput) return;
        
        const searchValue = searchInput.value.toLowerCase();
        const bankOptions = bankModal.querySelectorAll('.bank-option');
        
        bankOptions.forEach(option => {
            const bankName = option.querySelector('.bank-info strong').textContent.toLowerCase();
            if (bankName.includes(searchValue)) {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    // Reset the wizard
    function resetWizard() {
        currentStepIndex = 0;
        selectedCountry = 'GB';
        selectedBank = null;
        
        // Reset form fields
        const countrySelect = bankModal.querySelector('select[name="country"]');
        if (countrySelect) countrySelect.value = 'GB';
        
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
                
                // In a real implementation, this would submit the form data
                // For now, we'll just simulate a successful connection
                setTimeout(() => {
                    // Hide the modal
                    const modal = bootstrap.Modal.getInstance(bankModal);
                    modal.hide();
                    
                    // Show success message
                    if (typeof showToast === 'function') {
                        showToast('Bank connected successfully!', 'success');
                    }
                    
                    // Reset form for next use
                    setTimeout(resetWizard, 500);
                    
                    // Reset button state
                    submitBtn.innerHTML = 'Connect';
                    submitBtn.disabled = false;
                }, 2000);
            }
        });
    }
    
    // Initialize the wizard when the modal is shown
    bankModal.addEventListener('show.bs.modal', resetWizard);
});