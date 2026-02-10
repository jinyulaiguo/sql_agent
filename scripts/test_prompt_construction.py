
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from agent.base_agent import TextToSQLAgent

def test_prompt():
    print("--- Testing System Prompt Construction ---")
    
    agent = TextToSQLAgent()
    
    # Check if examples are loaded
    if hasattr(agent, 'few_shot_examples') and agent.few_shot_examples:
        print(f"✅ Loaded {len(agent.few_shot_examples)} few-shot examples.")
    else:
        print("❌ Failed to load few-shot examples.")
        
    # Construct prompt
    prompt = agent._construct_system_prompt("Testing query")
    
    print("\n--- Generated Prompt Preview (Last 500 chars) ---")
    print(prompt[-500:])
    
    if "参考示例 (Few-shot Examples):" in prompt:
        print("\n✅ Few-shot section found in prompt.")
    else:
        print("\n❌ Few-shot section MISSING in prompt.")

if __name__ == "__main__":
    test_prompt()
