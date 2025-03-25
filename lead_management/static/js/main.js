// Main JavaScript for Lead Management System

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar on mobile
    const sidebarToggleButton = document.querySelector('.navbar-toggler');
    if (sidebarToggleButton) {
        sidebarToggleButton.addEventListener('click', function() {
            document.querySelector('#sidebar').classList.toggle('show');
        });
    }

    // Automatically dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 500);
            }
        }, 5000);
    });

    // Date range picker initialization for report filters
    const periodSelect = document.getElementById('period-select');
    if (periodSelect) {
        const dateRangeFields = document.querySelectorAll('.date-range-fields');
        
        function toggleDateFields() {
            if (periodSelect.value === 'custom') {
                dateRangeFields.forEach(field => field.style.display = 'block');
            } else {
                dateRangeFields.forEach(field => field.style.display = 'none');
            }
        }
        
        // Initial toggle
        toggleDateFields();
        
        // Toggle on change
        periodSelect.addEventListener('change', toggleDateFields);
    }
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
    
    // Dynamic form handling for project selection in payment form
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    const projectSelect = document.getElementById('id_project');
    
    if (projectId && projectSelect) {
        projectSelect.value = projectId;
    }
    
    // Calculate remaining amount for project payments
    const budgetField = document.getElementById('id_budget');
    const amountPaidField = document.getElementById('id_amount_paid');
    const remainingField = document.getElementById('id_remaining');
    
    if (budgetField && amountPaidField && remainingField) {
        function calculateRemaining() {
            const budget = parseFloat(budgetField.value) || 0;
            const amountPaid = parseFloat(amountPaidField.value) || 0;
            const remaining = Math.max(0, budget - amountPaid);
            remainingField.value = remaining.toFixed(2);
        }
        
        budgetField.addEventListener('input', calculateRemaining);
        amountPaidField.addEventListener('input', calculateRemaining);
        calculateRemaining();
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Time-related functions for attendance page
    const currentTimeElement = document.getElementById('current-time');
    if (currentTimeElement) {
        function updateTime() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            
            currentTimeElement.textContent = `${hours}:${minutes}:${seconds}`;
        }
        
        // Update time every second
        updateTime();
        setInterval(updateTime, 1000);
    }
    
    // Project payment progress bar calculations
    const paymentProgressBars = document.querySelectorAll('.payment-progress');
    paymentProgressBars.forEach(function(progressBar) {
        const budget = parseFloat(progressBar.dataset.budget) || 0;
        const paid = parseFloat(progressBar.dataset.paid) || 0;
        
        if (budget > 0) {
            const percentage = Math.min(100, (paid / budget) * 100);
            const bar = progressBar.querySelector('.progress-bar');
            
            if (bar) {
                bar.style.width = percentage + '%';
                bar.setAttribute('aria-valuenow', percentage);
                bar.textContent = percentage.toFixed(1) + '%';
                
                if (percentage >= 100) {
                    bar.classList.add('bg-success');
                    bar.classList.remove('bg-warning', 'bg-danger');
                } else if (percentage > 0) {
                    bar.classList.add('bg-warning');
                    bar.classList.remove('bg-success', 'bg-danger');
                } else {
                    bar.classList.add('bg-danger');
                    bar.classList.remove('bg-success', 'bg-warning');
                }
            }
        }
    });
    
    // Client search functionality
    const clientSearchInput = document.getElementById('client-search');
    if (clientSearchInput) {
        const clientRows = document.querySelectorAll('.client-row');
        
        clientSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            clientRows.forEach(function(row) {
                const clientName = row.dataset.name.toLowerCase();
                const clientCompany = row.dataset.company.toLowerCase();
                const clientEmail = row.dataset.email.toLowerCase();
                const clientPhone = row.dataset.phone.toLowerCase();
                
                if (clientName.includes(searchTerm) || 
                    clientCompany.includes(searchTerm) || 
                    clientEmail.includes(searchTerm) || 
                    clientPhone.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});
