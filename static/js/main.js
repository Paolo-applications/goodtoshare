document.addEventListener('DOMContentLoaded', () => {
    console.log("FoodShare JS Loaded");

    // Check user login status on page load
    checkLoginStatus();

    // Add event listeners for login, registration, logout
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        registrationForm.addEventListener('submit', handleRegistration);
    }

    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }

    // More specific event listeners for other functionalities will be added later
    // e.g., loading meals, handling purchases, etc.
});

async function checkLoginStatus() {
    try {
        const response = await fetch('/@me');
        const data = await response.json();

        const loggedInUserDiv = document.getElementById('loggedInUser');
        const guestUserDiv = document.getElementById('guestUser');
        const userSpecificContent = document.querySelectorAll('.user-specific-content'); // Content to show/hide

        if (response.ok && data.user_id) {
            console.log("User logged in:", data);
            if (loggedInUserDiv) {
                loggedInUserDiv.innerHTML = `
                    <p>Welcome, ${data.username}!</p>
                    <button id="logoutButton" class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">Logout</button>
                `;
                loggedInUserDiv.style.display = 'block';
                // Re-add event listener for the new logout button
                document.getElementById('logoutButton').addEventListener('click', handleLogout);
            }
            if (guestUserDiv) guestUserDiv.style.display = 'none';
            userSpecificContent.forEach(el => el.style.display = 'block'); // Show user-specific sections

            // Store user info globally or pass it around as needed
            window.currentUser = data;

            // Potentially trigger other functions that depend on user being logged in
            // e.g., loadUserOrders(), loadUserDonations() if on relevant pages

        } else {
            console.log("User not logged in or error:", data.message);
            if (loggedInUserDiv) loggedInUserDiv.style.display = 'none';
            if (guestUserDiv) guestUserDiv.style.display = 'block';
            userSpecificContent.forEach(el => el.style.display = 'none'); // Hide user-specific sections
            window.currentUser = null;
        }
    } catch (error) {
        console.error("Error checking login status:", error);
        // Handle network errors or server being down
        const loggedInUserDiv = document.getElementById('loggedInUser');
        const guestUserDiv = document.getElementById('guestUser');
        if (loggedInUserDiv) loggedInUserDiv.style.display = 'none';
        if (guestUserDiv) guestUserDiv.style.display = 'block'; // Show guest options
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const username = event.target.username.value;
    const password = event.target.password.value;
    const messageDiv = document.getElementById('loginMessage');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        if (response.ok) {
            if(messageDiv) messageDiv.textContent = "Login successful!";
            checkLoginStatus(); // Update UI
            // Potentially redirect or close modal
            closeAuthModal();
        } else {
            if(messageDiv) messageDiv.textContent = `Error: ${data.message}`;
        }
    } catch (error) {
        console.error("Login error:", error);
        if(messageDiv) messageDiv.textContent = "Login request failed.";
    }
}

async function handleRegistration(event) {
    event.preventDefault();
    const username = event.target.username.value;
    const password = event.target.password.value;
    const isBusiness = event.target.isBusiness ? event.target.isBusiness.checked : false; // Optional field
    const messageDiv = document.getElementById('registrationMessage');

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, is_business: isBusiness }),
        });
        const data = await response.json();
        if (response.ok) {
            if(messageDiv) messageDiv.textContent = "Registration successful! Please log in.";
            // Optionally auto-login or redirect to login form/modal
            showLoginModal(); // Assuming a function to switch to login view
        } else {
            if(messageDiv) messageDiv.textContent = `Error: ${data.message}`;
        }
    } catch (error) {
        console.error("Registration error:", error);
        if(messageDiv) messageDiv.textContent = "Registration request failed.";
    }
}

async function handleLogout() {
    const messageDiv = document.getElementById('logoutMessage'); // Or a general message area
    try {
        const response = await fetch('/logout', { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            if(messageDiv) messageDiv.textContent = "Logout successful!";
            checkLoginStatus(); // Update UI
            // Potentially redirect to homepage
        } else {
            if(messageDiv) messageDiv.textContent = `Error: ${data.message}`;
        }
    } catch (error) {
        console.error("Logout error:", error);
        if(messageDiv) messageDiv.textContent = "Logout request failed.";
    }
}


// Utility functions for modals (example)
function showLoginModal() {
    // Logic to display your login modal
    // For example, if you have a modal with id 'authModal' and want to show login form
    const authModal = document.getElementById('authModal');
    if (authModal) {
        document.getElementById('loginFormContainer').style.display = 'block';
        document.getElementById('registrationFormContainer').style.display = 'none';
        authModal.style.display = 'flex'; // Assuming it's a flex container for centering
    }
}

function showRegistrationModal() {
    // Logic to display your registration modal
    const authModal = document.getElementById('authModal');
    if (authModal) {
        document.getElementById('loginFormContainer').style.display = 'none';
        document.getElementById('registrationFormContainer').style.display = 'block';
        authModal.style.display = 'flex';
    }
}

function closeAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.style.display = 'none';
    }
    // Clear any messages
    const loginMessage = document.getElementById('loginMessage');
    if(loginMessage) loginMessage.textContent = '';
    const regMessage = document.getElementById('registrationMessage');
    if(regMessage) regMessage.textContent = '';
}

// Example: Add event listeners to buttons that would open these modals
document.addEventListener('DOMContentLoaded', () => {
    // ... (other DOMContentLoaded setup)

    const openLoginModalButton = document.getElementById('openLoginModal');
    if (openLoginModalButton) {
        openLoginModalButton.addEventListener('click', showLoginModal);
    }

    const openRegisterModalButton = document.getElementById('openRegisterModal');
    if (openRegisterModalButton) {
        openRegisterModalButton.addEventListener('click', showRegistrationModal);
    }

    // Close modal if background is clicked (optional)
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.addEventListener('click', (event) => {
            if (event.target === authModal) { // Clicked on modal backdrop
                closeAuthModal();
            }
        });
    }

    const switchToRegisterButton = document.getElementById('switchToRegister');
    if (switchToRegisterButton) {
        switchToRegisterButton.addEventListener('click', (e) => {
            e.preventDefault();
            showRegistrationModal();
        });
    }

    const switchToLoginButton = document.getElementById('switchToLogin');
    if (switchToLoginButton) {
        switchToLoginButton.addEventListener('click', (e) => {
            e.preventDefault();
            showLoginModal();
        });
    }

    const closeAuthModalButton = document.getElementById('closeAuthModal');
    if(closeAuthModalButton) {
        closeAuthModalButton.addEventListener('click', closeAuthModal);
    }
});
