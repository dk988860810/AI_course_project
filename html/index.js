function handleLogin(event) {
    event.preventDefault();
    const identity = document.getElementById('identity').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // 這裡編寫登入驗證邏輯
    // ...

    if (username === 'admin' && password === 'password') {
        alert('登入成功！');
    } else {
        alert('用戶名或密碼錯誤！');
    }
}

function showRegistrationForm() {
    const registrationForm = document.getElementById('registration-form');
    registrationForm.style.display = 'block';
}

function handleRegistration(event) {
    event.preventDefault();
    const newUsername = document.getElementById('new-username').value;
    const newPassword = document.getElementById('new-password').value;

    // 這裡編寫註冊邏輯
    // ...

    alert(`註冊成功！新賬號為 ${newUsername}`);
}