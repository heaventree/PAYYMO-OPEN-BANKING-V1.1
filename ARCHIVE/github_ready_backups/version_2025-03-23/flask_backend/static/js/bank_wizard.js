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
    const bankContainer = bankConnectionModal.querySelector('.bank-options-container');
    const countryFilter = document.getElementById('bankCountryFilter');
    const bankSearchInput = document.getElementById('bankSearchInput');
    
    let currentStep = 1;
    const totalSteps = steps.length;
    const availableBanks = [];
    let selectedBankId = null;
    
    console.log(`Found ${steps.length} steps and ${stepContents.length} step contents`);
    
    // Fetch available banks from API
    fetchAvailableBanks();
    
    // Add event listeners for search and filter
    if (bankSearchInput) {
        bankSearchInput.addEventListener('input', filterBanks);
    }
    
    if (countryFilter) {
        countryFilter.addEventListener('change', function() {
            fetchAvailableBanks(this.value);
        });
    }
    
    function fetchAvailableBanks(country = 'GB') {
        console.log(`Fetching banks for country: ${country}`);
        
        // Show loading state
        if (bankContainer) {
            bankContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading available banks...</p></div>';
        }
        
        // Make API request to get banks
        fetch(`/api/gocardless/banks?country=${country}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.banks) {
                    availableBanks.length = 0; // Clear array
                    availableBanks.push(...data.banks); // Add new banks
                    console.log(`Loaded ${availableBanks.length} banks`);
                    renderBankOptions();
                } else {
                    console.error('Failed to load banks:', data);
                    if (bankContainer) {
                        bankContainer.innerHTML = '<div class="alert alert-danger">Failed to load banks. Please try again later.</div>';
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching banks:', error);
                if (bankContainer) {
                    bankContainer.innerHTML = '<div class="alert alert-danger">Error loading banks. Please try again later.</div>';
                }
            });
    }
    
    function renderBankOptions() {
        if (!bankContainer) return;
        
        if (availableBanks.length === 0) {
            bankContainer.innerHTML = '<div class="alert alert-info">No banks available for this selection.</div>';
            return;
        }
        
        let html = '';
        availableBanks.forEach(bank => {
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card bank-option h-100 cursor-pointer border-2" data-bank-id="${bank.id}">
                        <div class="card-body text-center">
                            <img src="${bank.logo || 'https://via.placeholder.com/80x80.png?text=Bank'}" 
                                 alt="${bank.name}" class="bank-logo mb-2" style="max-height: 40px; max-width: 80%;">
                            <h6 class="mb-1">${bank.name}</h6>
                            <p class="small text-muted mb-0">${bank.country || ''}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        bankContainer.innerHTML = html;
        
        // Re-initialize bank options
        const bankOptions = bankConnectionModal.querySelectorAll('.bank-option');
        console.log(`Rendered ${bankOptions.length} bank options`);
        
        // Handle bank selection
        bankOptions.forEach(option => {
            option.addEventListener('click', function() {
                console.log('Bank option clicked');
                // Remove selection from all options
                bankOptions.forEach(opt => opt.classList.remove('border-primary'));
                
                // Add selection to clicked option
                this.classList.add('border-primary');
                
                // Store selected bank ID
                selectedBankId = this.dataset.bankId;
                console.log(`Selected bank ID: ${selectedBankId}`);
                
                // Enable next button if disabled
                if (nextButton) {
                    nextButton.disabled = false;
                    console.log('Next button enabled');
                }
                
                // Get selected bank details
                const selectedBank = availableBanks.find(bank => bank.id === selectedBankId);
                if (!selectedBank) return;
                
                const bankName = selectedBank.name;
                
                // Update bank name in the authorization step
                const authorizeHeader = bankConnectionModal.querySelector('.step-2 h5');
                if (authorizeHeader) {
                    authorizeHeader.textContent = `Connect to ${bankName}`;
                    console.log(`Updated header to: Connect to ${bankName}`);
                }
                
                // Update bank preview in step 2
                const bankNameEl = bankConnectionModal.querySelector('.bank-preview .bank-name');
                if (bankNameEl) {
                    bankNameEl.textContent = bankName;
                }
                
                // Update bank preview text
                const bankPreviewText = bankConnectionModal.querySelector('.bank-preview p');
                if (bankPreviewText) {
                    bankPreviewText.textContent = `You'll be redirected to ${bankName}'s secure login page`;
                }
                
                // Update connected account in step 3
                const connectedBankName = bankConnectionModal.querySelector('.connected-account h6');
                if (connectedBankName) {
                    connectedBankName.textContent = bankName;
                }
                
                // Update bank logo in previews if available
                const bankLogo = selectedBank.logo;
                if (bankLogo) {
                    const previewLogos = bankConnectionModal.querySelectorAll('.bank-preview-logo');
                    previewLogos.forEach(logo => {
                        logo.src = bankLogo;
                        logo.style.display = 'inline-block';
                    });
                }
            });
        });
    }
    
    function filterBanks() {
        if (!bankSearchInput || !bankContainer) return;
        
        const searchTerm = bankSearchInput.value.toLowerCase().trim();
        console.log(`Filtering banks by search term: "${searchTerm}"`);
        
        // If search is empty, show all banks
        if (!searchTerm) {
            renderBankOptions();
            return;
        }
        
        // Filter banks by name
        const filteredBanks = availableBanks.filter(bank => 
            bank.name.toLowerCase().includes(searchTerm));
        
        // Create a temporary array with filtered banks
        const tempBanks = [...availableBanks]; // Save original
        availableBanks.length = 0; // Clear array
        availableBanks.push(...filteredBanks); // Add filtered banks
        
        // Render filtered banks
        renderBankOptions();
        
        // Restore original banks array
        availableBanks.length = 0;
        availableBanks.push(...tempBanks);
    }
    
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