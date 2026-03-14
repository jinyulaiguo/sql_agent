"""Agent 核心模块 —— ReAct 循环

实现 ReAct (Reasoning and Acting) Agent，通过 LLM function calling
与工具函数交互，完成 Text-to-SQL 的推理-执行循环。
"""

from openai import AsyncOpenAI
from config.settings import get_settings
from agent.prompts import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.tools import list_tables_tool, get_schema_tool, execute_sql_tool
from loguru import logger
import json
import os
import asyncio
from typing import AsyncGenerator, Any

class TextToSQLAgent:
    """Text-to-SQL ReAct Agent"""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
        )
        self.model = self.settings.model_name
        self.base_system_prompt = TEXT_TO_SQL_SYSTEM_PROMPT

        # OpenAI function calling 工具定义
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_tables_tool",
                    "description": (
                        "List database table names for semantic discovery. "
                        "WARNING: DO NOT use this tool for questions involving 'record count', 'data volume', or 'top/bottom' tables. "
                        "For quantitative queries, you MUST write SQL to query information_schema or use COUNT(*)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_query": {
                                "type": "string",
                                "description": "Optional search term. Leave BLANK to list ALL tables in the database.",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Max results for semantic search. Defaults to 5. NOT for sorting by data volume.",
                                "default": 5
                            }
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_schema_tool",
                    "description": "Get detailed schema (DDL + comments) for specific tables.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of table names to inspect.",
                            }
                        },
                        "required": ["table_names"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_sql_tool",
                    "description": "Execute a SELECT SQL query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "The SELECT SQL query to execute.",
                            }
                        },
                        "required": ["sql_query"],
                    },
                },
            },
        ]

        # 工具函数映射
        self.tool_map = {
            "list_tables_tool": list_tables_tool,
            "get_schema_tool": get_schema_tool,
            "execute_sql_tool": execute_sql_tool,
        }

        self._load_few_shot_examples()

    def _load_few_shot_examples(self):
        """加载 Few-shot 示例"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(current_dir, "../data/few_shot_examples.json")

            if os.path.exists(data_path):
                with open(data_path, "r", encoding="utf-8") as f:
                    self.few_shot_examples = json.load(f)
            else:
                self.few_shot_examples = []
                logger.warning(f"Few-shot 示例文件不存在: {data_path}")
        except Exception as e:
            logger.warning(f"加载 Few-shot 示例失败: {e}")
            self.few_shot_examples = []

    def _construct_system_prompt(self) -> str:
        """构建动态 System Prompt（含 Few-shot 示例）"""
        prompt = self.base_system_prompt

        if self.few_shot_examples:
            examples_text = "\n\n参考示例 (Few-shot Examples):\n"
            for ex in self.few_shot_examples[:2]:
                examples_text += (
                    f"Q: {ex['question']}\n"
                    f"SQL: {ex['sql']}\n"
                    f"Thought: {ex['thought']}\n\n"
                )
            prompt += examples_text

        return prompt

    async def stream_run(self, user_query: str, history: list[dict] = None) -> AsyncGenerator[str, list[dict]]:
        """
        Agent 流式主循环：通过 SSE 数据块逐步推回。

        Yields:
            JSON string of events (e.g. `{"event": "content", "data": "..."}`)

        Returns:
            list[dict]: 执行完毕后的完整的 messages 列表
        """
        if history:
            messages = history + [{"role": "user", "content": user_query}]
        else:
            system_prompt = self._construct_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ]
        logger.info(f"用户查询 (Stream): {user_query}")

        max_turns = 100
        for turn in range(max_turns):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    stream=True, # 开启流式
                )

                # 用于拼接当前轮次的流式输出
                current_content = ""
                # 用于拼接 Function Calling 参数
                tool_calls_dict = {}

                async for chunk in response:
                    delta = chunk.choices[0].delta
                    
                    # 1. 文本输出流
                    if delta.content is not None:
                        current_content += delta.content
                        if delta.content:
                            yield json.dumps({"event": "content", "data": delta.content}, ensure_ascii=False)
                    
                    # 2. Function Calling 流解析
                    if delta.tool_calls:
                        for tool_call_chunk in delta.tool_calls:
                            idx = tool_call_chunk.index
                            if idx not in tool_calls_dict:
                                tool_calls_dict[idx] = {
                                    "id": tool_call_chunk.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call_chunk.function.name,
                                        "arguments": ""
                                    }
                                }
                            if tool_call_chunk.function.arguments:
                                tool_calls_dict[idx]["function"]["arguments"] += tool_call_chunk.function.arguments

                # 将组装好的 message 添加入历史
                assistant_message = {"role": "assistant"}
                if current_content:
                    assistant_message["content"] = current_content
                
                # 情况1: LLM 决定调用工具
                if tool_calls_dict:
                    tool_calls = list(tool_calls_dict.values())
                    assistant_message["tool_calls"] = tool_calls
                    if not current_content:
                        assistant_message["content"] = None
                    messages.append(assistant_message)

                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        arguments_str = tool_call["function"]["arguments"]
                        try:
                            arguments = json.loads(arguments_str)
                        except json.JSONDecodeError:
                            arguments = {}
                            
                        logger.info(f"调用工具: {function_name}，参数: {arguments}")
                        yield json.dumps({"event": "tool", "data": f"执行动作: {function_name}"}, ensure_ascii=False)

                        func = self.tool_map.get(function_name)
                        if func:
                            try:
                                # 对于同步工具函数，使用 run_in_executor 避免阻塞事件循环
                                loop = asyncio.get_event_loop()
                                result = await loop.run_in_executor(None, lambda: func(**arguments))
                            except Exception as e:
                                result = f"工具执行错误: {e}"
                        else:
                            result = "错误: 未知工具。"

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "name": function_name,
                                "content": str(result),
                            }
                        )
                    continue

                # 情况2: 无工具调用，推理结束
                messages.append(assistant_message)
                logger.info("Agent 完成推理。")
                yield json.dumps({"event": "final_messages", "data": messages}, ensure_ascii=False)
                return

            except Exception as e:
                logger.error(f"Agent 流式执行错误: {e}")
                yield json.dumps({"event": "error", "data": "抱歉，处理您的问题时发生了内部错误，请稍后重试。"}, ensure_ascii=False)
                return

        yield json.dumps({"event": "error", "data": "达到最大推理轮数，未能生成最终回答。"}, ensure_ascii=False)
        return

    def run(self, user_query: str, history: list[dict] = None) -> tuple[str, list[dict]]:
        """保留老的同步接口用于兼容老的脚本"""


# 全局 Agent 实例（client 和工具定义共享，messages 每次 run 独立）
agent = TextToSQLAgent()
