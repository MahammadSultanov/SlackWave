document.addEventListener('DOMContentLoaded', function() {
    // Login Form Submission
    // Login form submission handling
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorMessage = document.getElementById('errorMessage');
        
        try {
            const response = await fetch('{{ url_for("auth.login") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                window.location.href = '{{ url_for("slack.index") }}';
            } else {
                errorMessage.textContent = data.message;
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            errorMessage.textContent = 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
        }
    });     
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

    // Message Form Submission
    const messageForm = document.getElementById('smsForm');
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const selectedChannels = Array.from(channelCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedChannels.length === 0) {
            showNotification('Please select at least one channel', 'error');
            return;
        }

        const messageInput = document.getElementById('message');
        const message = messageInput.value.trim();
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        if (!message && !file) {
            showNotification('Please enter a message or select a file', 'error');
            return;
        }

        const formData = new FormData();
        if (message) {
            formData.append('message', message);
        }
        if (file) {
            formData.append('photo', file);
        }
        selectedChannels.forEach(channel => {
            formData.append('channels', channel);
        });

        const submitButton = messageForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        try {
            const response = await fetch('/sms-sender', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                showNotification('Message sent successfully!', 'success');
                messageForm.reset();
                // Uncheck all checkboxes
                channelCheckboxes.forEach(cb => cb.checked = false);
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
                fileUploadArea.querySelector('p').textContent = 'Drag and drop files here or';
                characterCounter.textContent = `0/${maxLength} characters`;
            } else {
                showNotification(result.message || 'Failed to send message', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error sending message', 'error');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Send Message';
        }
    });

    // File upload handling
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.querySelector('.upload-btn');

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        const fileName = this.files[0]?.name;
        if (fileName) {
            fileUploadArea.querySelector('p').textContent = `Selected file: ${fileName}`;
        } else {
            fileUploadArea.querySelector('p').textContent = 'Drag and drop files here or';
        }
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

    // Character Counter
    const messageTextarea = document.getElementById('message');
    const characterCounter = document.querySelector('.character-counter');
    const maxLength = 512;


    // Character counter functionality and limit
    messageTextarea.addEventListener('input', function() {
        const currentLength = this.value.length;
        characterCounter.textContent = `${currentLength}/${maxLength} characters`;
        if (currentLength > maxLength) {
            this.value = this.value.substring(0, maxLength);
            characterCounter.textContent = `${maxLength}/${maxLength} characters`;
            showNotification('Message exceeds maximum length!', 'error');
        }
    });
});
