document.addEventListener('DOMContentLoaded', function() {
    // Channel selection handling
    const selectAllCheckbox = document.getElementById('selectAll');
    const channelCheckboxes = document.querySelectorAll('input[name="channels"]');

    selectAllCheckbox.addEventListener('change', function() {
        channelCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });

    // Update select all checkbox state when individual checkboxes change
    channelCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const allChecked = Array.from(channelCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(channelCheckboxes).some(cb => cb.checked);
            selectAllCheckbox.checked = allChecked;
            selectAllCheckbox.indeterminate = someChecked && !allChecked;
        });
    });

    // Email Form Submission
    const emailForm = document.getElementById('addToChannelForm');
    emailForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedChannels = Array.from(channelCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedChannels.length === 0) {
            showNotification('Please select at least one channel', 'error');
            return;
        }

        const emailInput = document.getElementById('channelEmail');
        const email = emailInput.value.trim();
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        if (!email && !file) {
            showNotification('Please enter a email or select a file', 'error');
            return;
        }

        const formData = new FormData();
        if (email) {
            formData.append('email', email);
        }
        if (file) {
            formData.append('table', file);
        }
        selectedChannels.forEach(channel => {
            formData.append('channels', channel);
        });

        const submitButton = emailForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

        try {
            const response = await fetch('/add-to-channel', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                showNotification('User added successfully!', 'success');
                emailForm.reset();
                // Uncheck all checkboxes
                channelCheckboxes.forEach(cb => cb.checked = false);
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
                // fileUploadArea.querySelector('p').textContent = 'Drag and drop Excel files here (.xlsx, .xls, .csv) or';
            } else {
                showNotification(result.email || 'Failed to add user', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error adding user', 'error');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-user-plus"></i> Add People';
        }
    });

     // File upload handling
     const fileUploadArea = document.querySelector('.file-upload-area');
     const fileInput = document.getElementById('fileInput');
     const uploadBtn = document.querySelector('.upload-btn');
     const excelFilename = document.getElementById('excel-filename');
     const excelRows = document.getElementById('excel-rows');
 
     fileInput.addEventListener('change', function() {
         const fileName = this.files[0]?.name;
         if (fileName) {
             fileUploadArea.querySelector('p').textContent = `Selected file: ${fileName}`;
         } else {
             fileUploadArea.querySelector('p').textContent = 'Drag and drop Excel files here (.xlsx, .xls, .csv) or';
         }
     });
 
     uploadBtn.addEventListener('click', () => {
         fileInput.click();
     });   

    // Notification function
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
            <button class="close-notification"><i class="fas fa-times"></i></button>
        `;
        
        const notificationCenter = document.querySelector('.notification-center');
        notificationCenter.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);

        // Close button functionality
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.remove();
        });
    }
        // Handle dependency issue
        const dependencyWarning = document.getElementById('dependency-warning');
        let currentMissingPackage = '';

        fileInput.addEventListener('change', async function() {
            const file = this.files[0];
            if (file) {
                fileUploadArea.querySelector('p').textContent = `Selected file: ${file.name}`;
                
                // Check if it's an Excel file
                if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')) {
                    // Create FormData and send to server for preview
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        const response = await fetch('/read-excel', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            dependencyWarning.style.display = 'none';
                            displayExcelPreview(result);
                            showNotification('Excel file loaded successfully', 'success');
                        } else { showNotification('Python paketleri yoxdu', 'error'); }
                    } catch (error) {
                        showNotification('Error processing Excel file', 'error');
                    }
                }
            } else {
                fileUploadArea.querySelector('p').textContent = 'Drag and drop Excel files here (.xlsx, .xls, .csv) or';
                dependencyWarning.style.display = 'none';
            }
        });

    // New email-related elements
    const emailList = document.getElementById('email-list');
    const emailsContainer = document.getElementById('emails-container');
    
    let extractedEmails = []; // Store extracted emails
    
    // Function to display Excel preview
    function displayExcelPreview(data) {
        excelFilename.textContent = data.filename;
        excelRows.textContent = data.row_count;
        
        // Create table header
        let tableHTML = '<thead><tr>';
        data.columns.forEach(column => {
            tableHTML += `<th>${column}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';
        
        // Create table rows for preview data
        data.preview.forEach(row => {
            tableHTML += '<tr>';
            data.columns.forEach(column => {
                tableHTML += `<td>${row[column] !== null && row[column] !== undefined ? row[column] : ''}</td>`;
            });
            tableHTML += '</tr>';
        });
        tableHTML += '</tbody>';
        

        // Handle extracted emails if any
        if (data.extracted_emails && data.extracted_emails.length > 0) {
            extractedEmails = data.extracted_emails;
            displayEmailList(data.extracted_emails);
        } else {
            emailList.style.display = 'none';
        }
    }
    // Function to display extracted emails
    function displayEmailList(emails) {
        // Update email count display
        document.getElementById('email-count').textContent = `(${emails.length})`;
        
        // Create list items for each email
        let listHTML = '';
        emails.forEach(email => {
            listHTML += `<li class="email-item">
                <input type="checkbox" class="email-checkbox" name="emails" value="${email}">
                <i class="fas fa-envelope"></i>
                <span>${email}</span>
            </li>`;
        });
        
        emailsContainer.innerHTML = listHTML;
        emailList.style.display = 'block';
        
        // Add button for selecting emails
        if (!document.getElementById('selectEmailsBtn')) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'email-buttons';
            buttonContainer.innerHTML = `
                <button type="button" id="selectAllEmailsBtn" class="btn btn-secondary">
                    <i class="fas fa-check-square"></i> Select All Emails
                </button>
                <button type="button" id="unselectAllEmailsBtn" class="btn btn-secondary">
                    <i class="fas fa-square"></i> Unselect All
                </button>
                <button type="button" id="selectEmailsBtn" class="btn btn-primary">
                    <i class="fas fa-plus-circle"></i> Add Selected Emails
                </button>
            `;
            emailList.insertBefore(buttonContainer, emailList.querySelector('.email-list-container'));
            
            // Add event listeners for the new buttons
            document.getElementById('selectAllEmailsBtn').addEventListener('click', function() {
                document.querySelectorAll('.email-checkbox').forEach(checkbox => {
                    checkbox.checked = true;
                });
            });
            
            document.getElementById('unselectAllEmailsBtn').addEventListener('click', function() {
                document.querySelectorAll('.email-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
            });
            
            document.getElementById('selectEmailsBtn').addEventListener('click', function() {
                updateEmailTextarea();
                showNotification('Selected emails added to the input field', 'success');
            });
        }
        
        // Add event listener to update textarea when checkboxes change
        const emailCheckboxes = document.querySelectorAll('.email-checkbox');
        emailCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // We don't automatically update the textarea now, only when the button is clicked
            });
        });
    }
    
    // Function to update the email textarea based on checked emails
    function updateEmailTextarea() {
        const checkedEmails = Array.from(document.querySelectorAll('.email-checkbox:checked'))
            .map(checkbox => checkbox.value);
        
        const emailTextarea = document.getElementById('channelEmail');
        // Append selected emails to existing content or set if empty
        if (emailTextarea.value.trim()) {
            const existingEmails = emailTextarea.value.split(/[\n,;]+/)
                .map(e => e.trim())
                .filter(e => e);
                
            // Combine existing and newly checked emails, remove duplicates
            const uniqueEmails = [...new Set([...existingEmails, ...checkedEmails])];
            emailTextarea.value = uniqueEmails.join('\n');
        } else {
            emailTextarea.value = checkedEmails.join('\n');
        }
    }

});