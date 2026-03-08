"""API 请求/响应数据模型"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求体"""
    message: str


class ChatResponse(BaseModel):
    """聊天响应体"""
    response: str
