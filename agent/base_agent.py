"""Agent 核心模块 —— ReAct 循环

实现 ReAct (Reasoning and Acting) Agent，通过 LLM function calling
与工具函数交互，完成 Text-to-SQL 的推理-执行循环。
"""

from openai import OpenAI
from config.settings import get_settings
from agent.prompts import TEXT_TO_SQL_SYSTEM_PROMPT
from agent.tools import list_tables_tool, get_schema_tool, execute_sql_tool
from loguru import logger
import json
import os


class TextToSQLAgent:
    """Text-to-SQL ReAct Agent"""

    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
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
                    "description": "List table names. Use filter_query to find relevant tables via RAG.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_query": {
                                "type": "string",
                                "description": "The user's question or keywords to filter tables.",
                            }
                        },
                        "required": ["filter_query"],
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

    def run(self, user_query: str, history: list[dict] = None) -> tuple[str, list[dict]]:
        """
        Agent 主循环：接收用户问题，通过 ReAct 循环调用工具，返回最终回答。

        Args:
            user_query: 用户的自然语言问题
            history: 可选，之前的压缩会话历史（system + user/assistant 对话）

        Returns:
            tuple[str, list[dict]]: (Agent 的最终回答, 完整的 messages 列表)
        """
        # 构建 messages：有历史则追加新问题，否则新建
        if history:
            messages = history + [{"role": "user", "content": user_query}]
        else:
            system_prompt = self._construct_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ]
        logger.info(f"用户查询: {user_query}")

        max_turns = 100
        for turn in range(max_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )

                message = response.choices[0].message
                messages.append(message)

                # 情况1: LLM 需要调用工具
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        logger.info(f"调用工具: {function_name}，参数: {arguments}")

                        func = self.tool_map.get(function_name)
                        if func:
                            try:
                                result = func(**arguments)
                            except Exception as e:
                                result = f"工具执行错误: {e}"
                        else:
                            logger.error(f"未知工具: {function_name}")
                            result = "错误: 未知工具。"

                        logger.info(
                            f"工具结果 ({function_name}): {str(result)[:100]}..."
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": str(result),
                            }
                        )
                    continue

                # 情况2: LLM 给出了最终回答
                else:
                    logger.info("Agent 完成推理。")
                    return message.content, messages

            except Exception as e:
                logger.error(f"Agent 执行错误: {e}")
                return "抱歉，处理您的问题时发生了内部错误，请稍后重试。", messages

        return "错误: 达到最大推理轮数，未能生成最终回答。", messages


# 全局 Agent 实例（client 和工具定义共享，messages 每次 run 独立）
agent = TextToSQLAgent()
