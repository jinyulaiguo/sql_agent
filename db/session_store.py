"""Redis 会话存储模块

管理多轮对话的会话历史，支持压缩存储和 TTL 自动过期。
"""

import json
import redis
from config.settings import get_settings
from loguru import logger


class SessionStore:
    """基于 Redis 的会话历史存储"""

    def __init__(self):
        settings = get_settings()
        self.client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        self.ttl = settings.session_ttl
        self.max_rounds = settings.max_history_rounds

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def get_history(self, session_id: str) -> list[dict] | None:
        """
        获取会话历史。

        Args:
            session_id: 会话 ID

        Returns:
            list[dict] | None: 历史 messages 列表，不存在则返回 None
        """
        try:
            data = self.client.get(self._key(session_id))
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"读取会话历史失败 [{session_id}]: {e}")
            return None

    def save_history(self, session_id: str, messages: list[dict]) -> None:
        """
        保存压缩后的会话历史到 Redis（带 TTL）。

        只保留 system + user + assistant 消息，丢弃 tool_call/tool_result，
        并截断为最近 N 轮，防止 Token 膨胀。

        Args:
            session_id: 会话 ID
            messages: Agent 运行后的完整 messages 列表
        """
        try:
            compressed = self._compress(messages)
            self.client.setex(
                self._key(session_id),
                self.ttl,
                json.dumps(compressed, ensure_ascii=False),
            )
            logger.debug(f"会话历史已保存 [{session_id}]，共 {len(compressed)} 条消息")
        except Exception as e:
            logger.error(f"保存会话历史失败 [{session_id}]: {e}")

    def _compress(self, messages: list[dict]) -> list[dict]:
        """
        压缩 messages：只保留 system/user/assistant，截断为最近 N 轮。

        Args:
            messages: 完整的 messages 列表（含 tool_call 等）

        Returns:
            list[dict]: 压缩后的 messages
        """
        system_msgs = []
        conversation = []

        for msg in messages:
            # msg 可能是 dict 或 OpenAI 的 Message 对象
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", None)
                content = getattr(msg, "content", "") or ""

            if role == "system":
                system_msgs = [{"role": "system", "content": content}]
            elif role in ("user", "assistant") and content:
                conversation.append({"role": role, "content": content})

        # 截断：每轮 = 1 user + 1 assistant = 2 条
        max_msgs = self.max_rounds * 2
        if len(conversation) > max_msgs:
            conversation = conversation[-max_msgs:]

        return system_msgs + conversation

    def delete_session(self, session_id: str) -> None:
        """删除指定会话"""
        try:
            self.client.delete(self._key(session_id))
        except Exception as e:
            logger.error(f"删除会话失败 [{session_id}]: {e}")


# 模块级单例
session_store = SessionStore()
