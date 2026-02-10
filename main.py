import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.base_agent import agent

def main():
    print("==========================================")
    print("🤖 Text-to-SQL Agent CLI")
    print("输入问题开始查询，输入 'exit' 或 'quit' 退出")
    print("==========================================\n")

    while True:
        try:
            user_input = input("\n👤 为了确保准确，请详细描述您的问题: ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
                
            print("\n🤖 Agent 思考中...")
            response = agent.run(user_input)
            
            print(f"\n✅ 回答:\n{response}")
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            logger.error(f"发生错误: {e}")

if __name__ == "__main__":
    main()
