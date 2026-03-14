"""FastAPI 后端入口

提供 Text-to-SQL Agent 的 HTTP API 接口。
"""

import uuid
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from models.api import ChatRequest
from models.auth import UserRegister, UserLogin, Token
from agent.base_agent import agent
from db.session_store import session_store
from db.engine import get_db, SessionLocal
from db.models import User
from security.auth import get_password_hash, verify_password, create_access_token, get_current_user
from config.logging import setup_logging
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Depends, status
import uvicorn

# 初始化日志
setup_logging()

# 初始化 FastAPI
app = FastAPI(title="Text-to-SQL Agent API", version="2.0.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"参数验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 认证相关接口 ---

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    
    # 创建新用户
    new_user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "注册成功", "user_id": new_user.id}


@app.post("/api/v1/auth/login", response_model=Token)
async def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """用户登录并返回 JWT"""
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 签发 Token
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"id": current_user.id, "username": current_user.username}


# --- 历史记录相关接口 ---

@app.get("/api/v1/sessions")
async def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的会话列表"""
    from db.models import ChatSession
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        {"id": s.id, "title": s.title or "新会话", "updated_at": s.updated_at}
        for s in sessions
    ]


@app.get("/api/v1/sessions/{session_id}")
async def get_session_detail(
    session_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """获取指定会话的完整历史记录"""
    from db.models import ChatSession, ChatMessage
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return {
        "id": session.id,
        "title": session.title,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ]
    }


# --- 对话相关接口 ---

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    接收用户消息并开始 SSE 流式返回 Agent 回答。
    支持多轮对话：首次不传 session_id（新建会话），追问时带上 session_id。
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 确定 session_id
    session_id = request.session_id or str(uuid.uuid4())

    # 获取历史会话（追问时）
    history = None
    if request.session_id:
        history = session_store.get_history(session_id)
        if history:
            logger.info(f"加载会话历史 [{session_id}]，共 {len(history)} 条消息")

    async def stream_generator():
        # 首先发送 session_id，让前端知道是在哪个会话上下文中
        yield f"data: {{\"event\": \"session\", \"data\": \"{session_id}\"}}\n\n"
        
        # 异步迭代代理运行
        messages = None
        try:
            async for chunk_str in agent.stream_run(request.message, history=history):
                try:
                    import json
                    chunk_data = json.loads(chunk_str)
                    if chunk_data.get("event") == "final_messages":
                        messages = chunk_data.get("data")
                        continue
                except:
                    pass
                yield f"data: {chunk_str}\n\n"
        except StopAsyncIteration:
            pass
        except Exception as e:
            logger.error(f"流式分发过程中发生错误: {e}")
            yield f"data: {{\"event\": \"error\", \"data\": \"系统内部错误\"}}\n\n"

        # 流处理完成后，持久化完整的上下文到 Redis 和 MySQL
        if messages:
            try:
                # 1. 保存到 Redis (用于快速上下文检索)
                session_store.save_history(session_id, messages)
                logger.info("对话历史已保存到 Redis")
                
                # 2. 保存到 MySQL (长期持久化)
                from db.models import ChatSession, ChatMessage
                with SessionLocal() as db:
                    # 确保会话存在
                    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
                    if not session:
                        # 如果是新会话，自动生成标题（取第一条用户消息的前 20 个字）
                        title = request.message[:20] + "..." if len(request.message) > 20 else request.message
                        session = ChatSession(id=session_id, user_id=current_user.id, title=title)
                        db.add(session)
                    else:
                        session.updated_at = datetime.now() # 自动更新触发
                    
                    # 为了简化，我们只同步这一轮新增的消息
                    # 或者清理后重写。这里采用“增量追加”逻辑会稍微复杂点（需要判断哪些是新的）
                    # 简单起见，我们先根据时间戳或清空重写。
                    # 由于 RAG 场景下 messages 是全量返回的，清空重写最稳妥。
                    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
                    for m in messages:
                        db.add(ChatMessage(
                            session_id=session_id,
                            role=m["role"],
                            content=m.get("content") or ""
                        ))
                    db.commit()
                logger.info("对话历史已同步至 MySQL")
            except Exception as e:
                logger.error(f"持久化历史记录失败: {e}")
                
        # 结束占位事件
        yield f"data: {{\"event\": \"done\"}}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
