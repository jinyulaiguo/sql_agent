"""FastAPI 后端入口

提供 Text-to-SQL Agent 的 HTTP API 接口。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.api import ChatRequest, ChatResponse
from agent.base_agent import agent
from config.logging import setup_logging
from loguru import logger
import uvicorn

# 初始化日志
setup_logging()

# 初始化 FastAPI
app = FastAPI(title="Text-to-SQL Agent API", version="1.0.0")

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

    使用 def（非 async def），FastAPI 会自动将其放入线程池执行，
    避免同步阻塞的 agent.run() 卡死整个事件循环。
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        response_text = agent.run(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后重试。")


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
