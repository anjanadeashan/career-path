// Auth operations
document.addEventListener('DOMContentLoaded', () => {
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
