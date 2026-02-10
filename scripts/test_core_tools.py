import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_core_tools():
    try:
        from tools.core_functions import list_tables_tool, get_schema_tool, execute_sql_tool
        
        print("\n--- 测试 list_tables_tool (带 RAG 过滤) ---")
        tables = list_tables_tool("查找客户发票")
        print(f"与 '查找客户发票' 相关的表: {tables}")
        
        if not tables:
            print("警告: RAG 未返回任何表，请检查向量库。")
            return

        print("\n--- 测试 get_schema_tool ---")
        # 假设我们想获取第一个找到的表的 Schema
        target_table = tables[0]
        schema = get_schema_tool([target_table])
        print(f"{target_table} 的 Schema:\n{schema[:500]}...") # 打印前 500 个字符

        print("\n--- 测试 execute_sql_tool (安全检查) ---")
        # 尝试一个危险查询
        result = execute_sql_tool("DROP TABLE Customer")
        print(f"DROP TABLE 的结果: {result}")

        print("\n--- 测试 execute_sql_tool (有效查询) ---")
        query = f"SELECT * FROM {target_table} LIMIT 5"
        result = execute_sql_tool(query)
        print(f"'{query}' 的结果:\n{result}")

    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    test_core_tools()
