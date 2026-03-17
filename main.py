"""命令行交互入口"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.logging import setup_logging
from agent.base_agent import agent
from loguru import logger

# 初始化日志
from config.settings import get_settings
setup_logging(level=get_settings().log_level)


def main():
    print("==========================================")
    print("🤖 Text-to-SQL Agent CLI")
    print("输入问题开始查询，输入 'exit' 或 'quit' 退出")
    print("==========================================\n")

    while True:
        try:
            user_input = input("\n👤 请描述您的问题: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("👋 再见！")
                break

            if not user_input:
                continue

            print("\n🤖 Agent 思考中...")
            response, _ = agent.run(user_input)

            print(f"\n✅ 回答:\n{response}")

        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            logger.error(f"发生错误: {e}")


if __name__ == "__main__":
    main()
