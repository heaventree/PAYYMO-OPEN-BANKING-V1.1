/**
 * Bank Connection Wizard
 * This script controls the bank connection wizard modal and steps
 */
document.addEventListener("DOMContentLoaded", function() {
    console.log("Bank wizard script loaded");
    
    // Check if the modal element exists
    const bankModal = document.getElementById('bankConnectionModal');
    if (!bankModal) {
        console.log("Bank connection modal not found");
        return;
    }
    
    // Initialize the wizard
    console.log("Initializing bank connection wizard");
    
    // Elements
    const steps = bankModal.querySelectorAll('.step');
    const stepContents = bankModal.querySelectorAll('.step-content');
    const nextButton = document.getElementById('bankWizardNextBtn');
    const progressBar = bankModal.querySelector('.progress-bar');
    
    console.log(`Found ${steps.length} steps and ${stepContents.length} step contents`);
    
    let currentStep = 1;
    const totalSteps = steps.length;
    let selectedBank = null;
    
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
            nextButton.disabled = !selectedBank;
        } else {
            nextButton.textContent = "Continue";
            nextButton.disabled = false;
        }
    }
    
    // Fetch available banks
    function fetchAvailableBanks(country = 'GB') {
        const bankOptionsContainer = bankModal.querySelector('.bank-options-container');
        
        // Show loading state
        bankOptionsContainer.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading available banks...</p>
            </div>
        `;
        
        // For demo purposes, we'll use mock data
        // In a real implementation, this would be an API call to GoCardless
        setTimeout(() => {
            // Mock data for demonstration
            const banks = [
                { id: 'hsbc_uk', name: 'HSBC UK', logo: 'https://via.placeholder.com/80x80.png?text=HSBC' },
                { id: 'barclays_uk', name: 'Barclays', logo: 'https://via.placeholder.com/80x80.png?text=Barclays' },
                { id: 'lloyds_uk', name: 'Lloyds Bank', logo: 'https://via.placeholder.com/80x80.png?text=Lloyds' },
                { id: 'natwest_uk', name: 'NatWest', logo: 'https://via.placeholder.com/80x80.png?text=NatWest' },
                { id: 'santander_uk', name: 'Santander UK', logo: 'https://via.placeholder.com/80x80.png?text=Santander' },
                { id: 'rbs_uk', name: 'Royal Bank of Scotland', logo: 'https://via.placeholder.com/80x80.png?text=RBS' },
                { id: 'halifax_uk', name: 'Halifax', logo: 'https://via.placeholder.com/80x80.png?text=Halifax' },
                { id: 'tsb_uk', name: 'TSB Bank', logo: 'https://via.placeholder.com/80x80.png?text=TSB' },
                { id: 'metro_uk', name: 'Metro Bank', logo: 'https://via.placeholder.com/80x80.png?text=Metro' }
            ];
            
            renderBankOptions(banks);
        }, 1000);
    }
    
    // Render bank options
    function renderBankOptions(banks) {
        const bankOptionsContainer = bankModal.querySelector('.bank-options-container');
        let html = '';
        
        banks.forEach(bank => {
            html += `
                <div class="col-lg-4 col-md-6 mb-3">
                    <div class="bank-option border rounded p-3 d-flex align-items-center cursor-pointer" data-bank-id="${bank.id}" data-bank-name="${bank.name}" data-bank-logo="${bank.logo}">
                        <div class="bank-logo bg-light rounded-circle d-flex align-items-center justify-content-center me-3">
                            <i data-lucide="landmark" style="width: 20px; height: 20px;"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">${bank.name}</h6>
                            <p class="mb-0 small text-muted">Personal & Business</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        bankOptionsContainer.innerHTML = html;
        
        // Initialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
        
        // Add event listeners to bank options
        const bankOptions = bankOptionsContainer.querySelectorAll('.bank-option');
        bankOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Remove active class from all options
                bankOptions.forEach(opt => opt.classList.remove('border-primary', 'bg-light'));
                
                // Add active class to selected option
                this.classList.add('border-primary', 'bg-light');
                
                // Store selected bank
                selectedBank = {
                    id: this.getAttribute('data-bank-id'),
                    name: this.getAttribute('data-bank-name'),
                    logo: this.getAttribute('data-bank-logo')
                };
                
                // Update bank preview in step 2
                updateBankPreview();
                
                // Enable the next button
                nextButton.disabled = false;
            });
        });
    }
    
    // Update bank preview in step 2
    function updateBankPreview() {
        if (!selectedBank) return;
        
        const bankName = bankModal.querySelector('.bank-name');
        const bankPreviewLogo = bankModal.querySelector('.bank-preview-logo');
        const bankLogoPlaceholder = bankModal.querySelector('.bank-preview .bank-logo');
        
        bankName.textContent = selectedBank.name;
        
        // Show bank logo if available, otherwise show placeholder
        if (selectedBank.logo) {
            bankPreviewLogo.src = selectedBank.logo;
            bankPreviewLogo.style.display = 'block';
            bankLogoPlaceholder.style.display = 'none';
        } else {
            bankPreviewLogo.style.display = 'none';
            bankLogoPlaceholder.style.display = 'inline-flex';
        }
    }
    
    // Initialize the bank search functionality
    function initBankSearch() {
        const searchInput = document.getElementById('bankSearchInput');
        const countryFilter = document.getElementById('bankCountryFilter');
        
        if (searchInput) {
            searchInput.addEventListener('input', filterBanks);
        }
        
        if (countryFilter) {
            countryFilter.addEventListener('change', function() {
                fetchAvailableBanks(this.value);
            });
        }
    }
    
    // Filter banks based on search input
    function filterBanks() {
        const searchInput = document.getElementById('bankSearchInput');
        const bankOptions = bankModal.querySelectorAll('.bank-option');
        
        if (!searchInput || !bankOptions.length) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        
        bankOptions.forEach(option => {
            const bankName = option.getAttribute('data-bank-name').toLowerCase();
            
            if (bankName.includes(searchTerm)) {
                option.closest('.col-lg-4').style.display = 'block';
            } else {
                option.closest('.col-lg-4').style.display = 'none';
            }
        });
    }
    
    // Handle the next button click
    nextButton.addEventListener('click', function() {
        if (currentStep < totalSteps) {
            currentStep++;
            updateStepIcons();
            showCurrentStep();
        } else {
            // Handle completion (step 3)
            // In a real implementation, this would close the modal and update the UI
            bankModal.querySelector('.modal-footer').innerHTML = `
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
            `;
        }
    });
    
    // Reset wizard when modal is hidden
    bankModal.addEventListener('hidden.bs.modal', function() {
        resetWizard();
    });
    
    // Reset the wizard state
    function resetWizard() {
        currentStep = 1;
        selectedBank = null;
        
        // Reset the UI
        updateStepIcons();
        showCurrentStep();
        
        // Reset the bank selection
        const bankOptions = bankModal.querySelectorAll('.bank-option');
        bankOptions.forEach(opt => opt.classList.remove('border-primary', 'bg-light'));
        
        // Reset the modal footer
        bankModal.querySelector('.modal-footer').innerHTML = `
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="bankWizardNextBtn" disabled>Continue to Authorization</button>
        `;
        
        // Re-attach event listener to the new button
        document.getElementById('bankWizardNextBtn').addEventListener('click', function() {
            if (currentStep < totalSteps) {
                currentStep++;
                updateStepIcons();
                showCurrentStep();
            } else {
                // Handle completion (step 3)
                bankModal.querySelector('.modal-footer').innerHTML = `
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Done</button>
                `;
            }
        });
    }
    
    // Initialize the wizard
    fetchAvailableBanks();
    initBankSearch();
    updateStepIcons();
    showCurrentStep();
});