// FIX: Target .login-container (not .container) to avoid Bootstrap conflict
const container = document.querySelector('.login-container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

if (registerBtn) {
    registerBtn.addEventListener('click', () => {
        container.classList.add('active');
    });
}

if (loginBtn) {
    loginBtn.addEventListener('click', () => {
        container.classList.remove('active');
    });
}
