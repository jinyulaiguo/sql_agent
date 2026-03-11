"""Agent 工具函数模块

定义 LLM 通过 function calling 调用的工具函数。
每个工具函数是底层模块（db、rag、security）的薄封装。
"""

from typing import List
from db.schema_extractor import schema_extractor
from db.executor import execute_query
from rag.retriever import retriever
from loguru import logger


def list_tables_tool(filter_query: str = None, top_k: int = 5) -> List[str]:
    """
    列出数据库中的表名。
    如果提供了 filter_query（例如用户的提问），则使用 RAG 语义检索相关表。
    如果不提供 filter_query，则返回数据库中的 **所有** 表名。

    Args:
        filter_query: 可选，用于 RAG 过滤的用户问题关键词。留空则返回所有表。
        top_k: 可选，使用 RAG 时返回的最相关表数量，默认 5。

    Returns:
        List[str]: 相关表名列表
    """
    try:
        if filter_query:
            logger.info(f"使用 RAG 检索相关表: '{filter_query}', top_k={top_k}")
            relevant_tables = retriever.retrieve_related_schemas(
                filter_query, n_results=top_k
            )
            if relevant_tables:
                return relevant_tables
            logger.warning("RAG 未返回结果，回退到显示所有表。")

        # 未提供 filter_query 或 RAG 失败时，返回全部表
        logger.info("未提供检索词，返回数据库全部表名")
        return schema_extractor.get_all_table_names()
    except Exception as e:
        logger.error(f"list_tables_tool 错误: {e}")
        return []


def get_schema_tool(table_names: List[str]) -> str:
    """
    获取指定表的详细 Schema（包含 DDL 和中文注释）。

    Args:
        table_names: 表名列表

    Returns:
        str: 所有表的文本化 Schema 信息
    """
    schemas_text = []
    try:
        for table in table_names:
            schema = schema_extractor.get_table_schema(table)
            schemas_text.append(schema.to_text_representation())
        return "\n\n".join(schemas_text)
    except Exception as e:
        logger.error(f"get_schema_tool 错误: {e}")
        return f"获取 Schema 时出错: {e}"


def execute_sql_tool(sql_query: str) -> str:
    """
    执行 SELECT SQL 查询并以 Markdown 表格形式返回结果。
    内部自动进行安全校验（sqlglot AST）和行数限制。

    Args:
        sql_query: 待执行的 SQL 查询

    Returns:
        str: Markdown 格式的结果或错误信息
    """
    logger.info(f"执行 SQL: {sql_query[:100]}...")
    return execute_query(sql_query)
