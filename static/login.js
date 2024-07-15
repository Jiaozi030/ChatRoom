// login.js
function register() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    // Encrypt the password using SHA-256
    const password_hash = CryptoJS.SHA256(password).toString();
    if (username && password) {
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password_hash: password_hash }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                alert('注册成功，请登录');
            } else {
                alert(data.detail);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const password_hash = CryptoJS.SHA256(password).toString();
    if (username && password) {
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password_hash: password_hash }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                accessToken = data.data.access_token;
                console.log(accessToken)
                // 存储token
                localStorage.setItem('username', username);
                localStorage.setItem('token', accessToken);
                let expires = new Date();
                expires.setTime(expires.getTime() + (30 * 60 * 1000)); // 设置为当前时间加上30分钟
                document.cookie = `token=${accessToken}; path=/; SameSite=Lax; expires=${expires.toString()}`;
                // document.cookie = `token=${accessToken}; path=/; SameSite=Lax; `;
                window.location.href = '/';
            } else {
                alert(data.detail);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
