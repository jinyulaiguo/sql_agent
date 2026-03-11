"""FastAPI 后端入口

提供 Text-to-SQL Agent 的 HTTP API 接口。
"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.api import ChatRequest, ChatResponse
from agent.base_agent import agent
from db.session_store import session_store
from config.logging import setup_logging
from loguru import logger
import uvicorn

# 初始化日志
setup_logging()

# 初始化 FastAPI
app = FastAPI(title="Text-to-SQL Agent API", version="2.0.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    接收用户消息并返回 Agent 回答。
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

    try:
        # 调用 Agent（带历史）
        response_text, messages = agent.run(request.message, history=history)

        # 保存压缩后的会话历史到 Redis
        session_store.save_history(session_id, messages)

        return ChatResponse(response=response_text, session_id=session_id)
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后重试。")


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
