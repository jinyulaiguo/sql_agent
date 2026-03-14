"""FastAPI 后端入口

提供 Text-to-SQL Agent 的 HTTP API 接口。
"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models.api import ChatRequest
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


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
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

        # 流处理完成后，持久化完整的上下文到 Redis
        if messages:
            try:
                session_store.save_history(session_id, messages)
                logger.info("对话历史已保存到 Redis")
            except Exception as e:
                logger.error(f"保存 Redis 历史失败: {e}")
                
        # 结束占位事件
        yield f"data: {{\"event\": \"done\"}}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
