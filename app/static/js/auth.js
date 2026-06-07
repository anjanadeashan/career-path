// Auth operations
document.addEventListener('DOMContentLoaded', () => {
    // Intercept OAuth implicit grant hash in the URL (e.g. after Google Login)
    const hash = window.location.hash;
    if (hash && hash.includes('access_token=')) {
        // Change button text or show loading to indicate login is processing
        const loginBtn = document.querySelector('button[type="submit"]');
        if (loginBtn) {
            loginBtn.innerHTML = 'Signing in with Google...';
            loginBtn.disabled = true;
        }
        
        // Parse the token from the URL hash
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        
        if (accessToken) {
            fetch('/auth/token_login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ access_token: accessToken })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.redirect) {
                    // Clear the hash from the URL and redirect to Profile
                    window.history.replaceState(null, null, window.location.pathname);
                    window.location.href = data.redirect;
                } else {
                    alert('Google Login Failed: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => console.error('Error verifying token:', err));
        }
    }

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            // Check if form has standard action or AJAX. 
            // We'll support standard POST by default, but write an AJAX handler if they want to build SPA components later.
            logger("Login form active");
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password')?.value;

            if (confirmPassword && password !== confirmPassword) {
                e.preventDefault();
                alert("Passwords do not match!");
            }
        });
    }
});

function logger(msg) {
    console.log(`[AuthHelper] ${msg}`);
}
