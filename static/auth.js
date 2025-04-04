// Toggle password visibility
function togglePasswordVisibility(inputId, toggleButton) {
    const passwordInput = document.getElementById(inputId);
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        toggleButton.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
    } else {
        passwordInput.type = "password";
        toggleButton.innerHTML = '<i class="fa-regular fa-eye"></i>';
    }
}

// Function to handle login submission
function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json().then(data => {
        if (response.ok) {
            window.location.href = "/";
        } else {
            errorMessage.textContent = data.message;
            errorMessage.style.display = 'block';
        }
    }))
    .catch(error => {
        errorMessage.textContent = 'An error occurred. Please try again.';
        errorMessage.style.display = 'block';
    });
    
    return false; // Prevent form submission
}

// Handle signup form submission
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const errorMessage = document.getElementById('signupErrorMessage');
        const username = document.getElementById('signupUsername').value;
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('signupConfirmPassword').value;
        const slackToken = document.getElementById('slackToken').value;
        
        if (password !== confirmPassword) {
            errorMessage.textContent = 'Passwords do not match';
            errorMessage.style.display = 'block';
            return;
        }
        
        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password,
                slack_token: slackToken
            })
        })
        .then(response => response.json().then(data => {
            if (response.ok) {
                window.location.href = '/';
            } else {
                errorMessage.textContent = data.message;
                errorMessage.style.display = 'block';
            }
        }))
        .catch(error => {
            errorMessage.textContent = 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
        });
    });
}