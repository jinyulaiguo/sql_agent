from openai import OpenAI
from config.settings import get_settings
from agent.prompts import TEXT_TO_SQL_SYSTEM_PROMPT
from tools.core_functions import list_tables_tool, get_schema_tool, execute_sql_tool
from loguru import logger
import json
import os

class TextToSQLAgent:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url
        )
        self.model = "deepseek-chat" # Check if user wants 'deepseek-coder' or 'deepseek-chat'
        self.base_system_prompt = TEXT_TO_SQL_SYSTEM_PROMPT
        self.messages = []
        
        # Tools definition for OpenAI API
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
                                "description": "The user's question or keywords to filter tables (e.g., 'customer invoices')."
                            }
                        },
                        "required": ["filter_query"]
                    }
                }
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
                                "description": "List of table names to inspect."
                            }
                        },
                        "required": ["table_names"]
                    }
                }
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
                                "description": "The SELECT SQL query to execute."
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            }
        ]

        # Function map for execution
        self.tool_map = {
            "list_tables_tool": list_tables_tool,
            "get_schema_tool": get_schema_tool,
            "execute_sql_tool": execute_sql_tool
        }
        
        self._load_few_shot_examples()

    def _load_few_shot_examples(self):
        """加载 Few-shot 示例"""
        try:
            # Assuming data is in day10/data/few_shot_examples.json relative to agent/base_agent.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(current_dir, "../data/few_shot_examples.json")
            
            if os.path.exists(data_path):
                with open(data_path, "r", encoding="utf-8") as f:
                    self.few_shot_examples = json.load(f)
            else:
                self.few_shot_examples = []
                logger.warning(f"Few-shot examples file not found at: {data_path}")
        except Exception as e:
            logger.warning(f"无法加载 Few-shot 示例: {e}")
            self.few_shot_examples = []

    def _construct_system_prompt(self, user_query: str) -> str:
        """
        构建动态 System Prompt，包含 Schema 信息和 Few-shot 示例
        """
        # 1. 基础 Prompt
        prompt = self.base_system_prompt
        
        # 2. 添加 Few-shot 示例 (如果有)
        if hasattr(self, 'few_shot_examples') and self.few_shot_examples:
            examples_text = "\n\n参考示例 (Few-shot Examples):\n"
            for ex in self.few_shot_examples[:2]: # 只展示前2个，避免 Token 过多
                 examples_text += f"Q: {ex['question']}\nSQL: {ex['sql']}\nThought: {ex['thought']}\n\n"
            prompt += examples_text

        return prompt

    def run(self, user_query: str):
        """
        The main loop for the agent to process a user query.
        """
        # Reset or append to history? For now, we keep history within a session could be good, 
        # but let's reset for fresh queries to save tokens unless 'chat' mode is requested.
        # Here we assume a single-turn or short-session usage.
        
        # Construct the system prompt dynamically for each run
        current_system_prompt = self._construct_system_prompt(user_query)
        
        # Clear messages for a new run, then add the dynamic system prompt and user query
        self.messages = [] 
        self.messages.append({"role": "system", "content": current_system_prompt})
        self.messages.append({"role": "user", "content": user_query})
        logger.info(f"User Query: {user_query}")

        max_turns = 10 # Prevent infinite loops
        turn_count = 0

        while turn_count < max_turns:
            turn_count += 1
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                self.messages.append(message) # Add assistant's thought/call to history

                # Case 1: The model wants to call a tool
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Agent executing tool: {function_name} with args: {arguments}")
                        
                        if function_name in self.tool_map:
                            func = self.tool_map[function_name]
                            try:
                                # Execute the tool
                                if function_name == "list_tables_tool":
                                    result = func(**arguments)
                                elif function_name == "get_schema_tool":
                                    result = func(**arguments)
                                elif function_name == "execute_sql_tool":
                                    result = func(**arguments)
                                else:
                                    result = "Error: Tool execution path not defined."
                            except Exception as e:
                                result = f"Error executing tool: {e}"
                                
                            logger.info(f"Tool Result ({function_name}): {str(result)[:100]}...")

                            # Append tool result to history
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": str(result)
                            })
                        else:
                            logger.error(f"Unknown tool: {function_name}")
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": "Error: Unknown tool."
                            })
                    
                    # Tool calls processed, loop back to let LLM see results and continue
                    continue
                
                # Case 2: The model has a final answer (no tool calls)
                else:
                    final_answer = message.content
                    logger.info("Agent finished.")
                    return final_answer

            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                return f"Agent met an error: {e}"
        
        return "Error: Maximum turns reached without a final answer."

agent = TextToSQLAgent()
