# -*- coding: utf-8 -*-

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict
from pojo.dto.UserDTO import UserDTO
from sqlalchemy.orm import Session
from datetime import datetime
from database import SessionLocal, User, Message
from fastapi.middleware.cors import CORSMiddleware
from jwt_handler import create_access_token, get_current_user

app = FastAPI()
# 创建应用实例并添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者指定前端的地址，如 "http://192.168.1.17:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        # print('添加连接用户', get_current_user(token))
        self.active_connections[token] = websocket
        # print("当前连接数", len(self.active_connections))

    def disconnect(self, token: str):
        if token in self.active_connections:
            websocket = self.active_connections[token]
            del self.active_connections[token]
            return websocket
        return None

    async def broadcast(self, message: str):
        for token, websocket in self.active_connections.items():
            # username = get_current_user(token)
            # print(f'广播发送给用户{username}')
            await websocket.send_text(message)


manager = ConnectionManager()


# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
async def register(userDTO: UserDTO, db: Session = Depends(get_db)):
    username = userDTO.username
    password_hash = userDTO.password_hash
    if not username or not password_hash:
        raise HTTPException(status_code=400, detail="用户名或密码不能为空")
    pass
    user = db.query(User).filter(User.username == username).first()

    if user:
        raise HTTPException(status_code=400, detail="用户名已被注册")
    # 创建新用户
    new_user = User(
        username=username,
        password_hash=password_hash,
        created_at=datetime.now(),
        last_login=datetime.now()
    )
    # 保存到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        'code': 200,
        'msg': "注册成功",
        "data": {}
    }


@app.post("/login")
async def login(userDTO: UserDTO, db: Session = Depends(get_db)):
    username = userDTO.username
    password_hash = userDTO.password_hash
    if not username or not password_hash:
        raise HTTPException(status_code=400, detail="用户名或密码不能为空")
    # 检查用户名是否已经存在
    # print(username, password_hash)
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=400, detail="该用户未注册")
    if password_hash != user.password_hash:
        raise HTTPException(status_code=400, detail="密码错误")

    access_token = create_access_token(data={"sub": user.username})

    # 更新last_login字段
    user.last_login = datetime.now()
    db.commit()

    return {
        'code': 200,
        'msg': "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer"
        }
    }


@app.get("/messages", dependencies=[Depends(get_current_user)])
async def get_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).order_by(Message.timestamp).all()
    return messages


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    username = get_current_user(token)  # 校验token并获取用户名
    await manager.connect(websocket, token=token)
    print(username, '开始连接成功')

    try:
        while True:
            data = await websocket.receive_text()
            message = Message(
                username=username,
                content=data,
                timestamp=datetime.now()
            )
            db.add(message)
            db.commit()
            formatted_time = message.timestamp.strftime("%Y/%m/%d %H:%M:%S")
            await manager.broadcast(f"{formatted_time}")
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        websocket = manager.disconnect(token)
        # if websocket:
        #     await websocket.close(code=1000, reason='Close Window')
        await manager.broadcast(f"用户{username}退出了聊天室")



@app.get("/login", response_class=HTMLResponse)
async def loginHandle(request: Request):
    with open("templates/login.html", "r", encoding='utf-8') as file:
        return HTMLResponse(content=file.read(), status_code=200)



@app.post("/logout")
async def logout_handle(request: Request):
    # 从Cookie中获取token
    token = request.cookies.get("token")
    # print("准备弹出的token", token)
    try:
        username = get_current_user(token)
    except Exception as e:
        return {
            "code": 400,
            "msg": "token异常",
            "data": {
                "token": token
            }
        }
    # print(token)
    # 从列表中拿出来
    websocket = manager.disconnect(token)
    # print("已经弹出", get_current_user(token))
    if websocket:
        # await websocket.close(code=1000, reason='Logged out')
        # await manager.broadcast(f"用户{username}退出了聊天室")
        return {
            "code": 200,
            "msg": "退出登录成功",
            "data": {
                "token": token
            }
        }
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")


# 配置根路径返回 index.html
@app.get("/", response_class=HTMLResponse)
async def indexHandle(request: Request):
    # 从Cookie中获取token
    token = request.cookies.get("token")
    print("进入主界面凭借的token", token)
    if token is None:  # 没有token
        # print("没有token")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    # token = auth_header.split(" ")[1]
    # 下面开始尝试校验token是否有效
    try:
        username = get_current_user(token)
    except Exception as e:
        print("token校验异常，可能时token已过时")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    # 下面就是拿到了有效的token的情况
    # print(f'成功解析{token}得到用户名{username}')
    with open("templates/index.html", "r", encoding='utf-8') as file:
        return HTMLResponse(content=file.read(), status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
