// 在页面加载完毕后添加事件监听器
window.onload = function() {
    var input = document.getElementById("messageInput");
    input.addEventListener("keypress", function(event) {
        if (event.keyCode === 13) { // 检查按键是否为回车键
            event.preventDefault(); // 阻止默认行为（不换行）
            document.querySelector('button[onclick="sendMessage()"]').click(); // 触发发送按钮点击
        }
    });
    // 滚动到底部
    // scrollToBottom();
};


let ws;
let username = localStorage.getItem("username")
let accessToken = localStorage.getItem("token");  //从当前的localStorage空间中 获取login页面村出的token
document.getElementById('userGreet').innerHTML = `欢迎您 <strong>${username}</strong>`;
loadMessages()  // 先加载数据库中的信息
startWebSocket()

function loadMessages() {
    // fetch时携带上token获取消息记录
    // console.log(`seeding... Bearer ${accessToken}`)
    fetch('/messages', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        }
    })
        .then(response => {
            //console.log('Response status:', response.status); // 添加日志以调试状态码
            if (response.status === 401 || response.status === 403) { // 识别到访问了未经过授权的资源 强制跳转到登入界面
                //console.log("123")
                // window.location.href = "/login";
                return; // 早退出
            }
            return response.json();
        })
        .then(data => {
            const messages = document.getElementById('messages');
            messages.innerHTML = ''; // 清空现有消息
            data.forEach(msg => {
                addOneMessage(new Date(msg.timestamp).toLocaleString())
                addOneMessage(`${msg.username}: ${msg.content}`)
            });
        })
        .catch(error => {
            console.error('Error:', error)
        });
}

function addOneMessage(data) {
        const messages = document.getElementById('messages');
        const message = document.createElement('div');
        const content = document.createTextNode(data);
        message.appendChild(content);
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
        // window.scrollTo(0, document.body.scrollHeight);
}


function startWebSocket() {
    ws = new WebSocket(`ws://192.168.1.17:8000/ws/${accessToken}`);
    ws.onmessage = function(event) {
        addOneMessage(event.data)
    };
}

function sendMessage() {
    const input = document.getElementById("messageInput");
    if (input.value) {
        ws.send(input.value);
        input.value = '';
    }
}

function logoutHandle() {
    // 可选：向服务器发送一个注销请求
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // 如果有必要，可以在 body 中发送更多信息
        body: JSON.stringify({ message: 'User has logged out' })
    })
    .then(response => {
        if (response.status === 200) {
            // 清除 localStorage 中的用户认证信息
            localStorage.removeItem('username');
            localStorage.removeItem('token');

            // 清除所有与认证相关的 cookies
            // 这里假设 token 是你存储的 cookie 的名称
            document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';

            // 重定向到登录页
            window.location.href = '/login';
        }
        return response.json()
    })
    .catch(error => {
        console.error('Logout failed:', error);
        // 即便注销失败，也可能需要重定向，取决于你的应用需求
        // 清除 localStorage 中的用户认证信息
        localStorage.removeItem('username');
        localStorage.removeItem('token');

        // 清除所有与认证相关的 cookies
        // 这里假设 token 是你存储的 cookie 的名称
        document.cookie = 'token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
        window.location.href = '/login';
    });


    // 如果不需要从服务器确认注销，可以直接重定向
    // window.location.href = '/login';
}
// function checkCookie() {
//     alert(document.cookie)
// }
