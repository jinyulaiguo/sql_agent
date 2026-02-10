import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_agent():
    try:
        from agent.base_agent import agent
        
        # Test Query 1: Simple Retrieval
        query1 = "查询所有的客户，显示前3个"
        print(f"\n--- 测试 Query 1: {query1} ---")
        answer1 = agent.run(query1)
        print(f"Agent 回答:\n{answer1}")

        # Test Query 2: Complex Retrieval (might need RAG)
        query2 = "统计每种流派的歌曲数量，按数量从高到低排序，只看前5名"
        print(f"\n--- 测试 Query 2: {query2} ---")
        answer2 = agent.run(query2)
        print(f"Agent 回答:\n{answer2}")
        
    except Exception as e:
        logger.error(f"Agent 测试失败: {e}")
        raise

if __name__ == "__main__":
    test_agent()
