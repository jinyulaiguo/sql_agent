from typing import List, Optional
from sqlalchemy import create_engine, text, inspect
from config.settings import get_settings
from rag.extractor import schema_extractor
from rag.retriever import retriever
from loguru import logger
import pandas as pd
import sqlglot
from sqlglot import exp

settings = get_settings()
engine = create_engine(settings.database_url)

def list_tables_tool(filter_query: str = None) -> List[str]:
    """
    列出数据库中的表名。
    如果提供了筛选问题（filter_query，例如用户的提问），则使用 RAG 检索相关表。
    """
    try:
        if filter_query:
            logger.info(f"正在使用 RAG 根据问题过滤表: {filter_query}")
            # 检索前 5 个相关表
            relevant_tables = retriever.retrieve_related_schemas(filter_query, n_results=5)
            if relevant_tables:
                return relevant_tables
            # 如果 RAG 没有返回结果，回退到返回所有表（或者根据情况返回空列表）
            logger.warning("RAG 未返回任何表，回退到显示所有表。")
        
        return schema_extractor.get_all_table_names()
    except Exception as e:
        logger.error(f"list_tables_tool 发生错误: {e}")
        return []

def get_schema_tool(table_names: List[str]) -> str:
    """
    获取指定表的详细 Schema（包含建表 DDL 和中文注释）。
    这是 schema_extractor 的封装。
    """
    schemas_text = []
    try:
        for table in table_names:
            schema = schema_extractor.get_table_schema(table)
            schemas_text.append(schema.to_text_representation())
        return "\n\n".join(schemas_text)
    except Exception as e:
        logger.error(f"get_schema_tool 发生错误: {e}")
        return f"获取 Schema 时出错: {e}"

def execute_sql_tool(sql_query: str) -> str:
    """
    执行 SELECT SQL 查询并以 Markdown 表格形式返回结果。
    强制执行只读模式和行数限制。
    """
    # 1. 安全检查：使用 sqlglot 解析
    try:
        # Parse the SQL to ensure it's valid and safe
        parsed = sqlglot.parse_one(sql_query)
        
        # Check if it's a SELECT statement
        if not isinstance(parsed, sqlglot.exp.Select):
             return "错误: 为确保安全，只允许执行 SELECT 查询。"
             
        # Check for modification statements (redundant with type check but safe)
        if isinstance(parsed, (sqlglot.exp.Delete, sqlglot.exp.Update, sqlglot.exp.Insert, sqlglot.exp.Drop)):
             return "错误:仅仅允许查询操作，禁止修改数据 (DROP, DELETE, UPDATE, INSERT)。"

    except sqlglot.errors.ParseError as e:
        return f"SQL 语法错误: {e}. 请检查你的 SQL 拼写。"

    # 2. 执行查询
    try:
        with engine.connect() as connection:
            # sqlglot parsed object can be converted back to string, but we use original for fidelity if valid
            # However, to be safe, we could use parsed.sql() but that might change formatting.
            # We stick to original query for execution after validation.
            
            result = connection.execute(text(sql_query))
            rows = result.fetchmany(20) 
            if not rows:
                return "未找到结果。"
                
            df = pd.DataFrame(rows, columns=result.keys())
            return df.to_markdown(index=False)
    except Exception as e:
        logger.error(f"SQL 执行错误: {e}")
        return f"数据库错误: {str(e)}. 请检查表名和字段名是否存在。"
