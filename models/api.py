"""API 请求/响应数据模型"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求体"""
    message: str
    session_id: str | None = None  # 首次为空（新会话），追问时带上


class ChatResponse(BaseModel):
    """聊天响应体"""
    response: str
    session_id: str  # 返回会话 ID，前端下次带回来
