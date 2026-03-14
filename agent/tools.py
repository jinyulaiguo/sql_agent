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
    【核心侦查工具】列出数据库中的表名，用于模糊发现和语义定位。
    当你完全不清楚数据库里有什么表，或者需要将模糊的业务词汇映射到实际表名时使用。
    
    注意：
    - 此工具仅返回表名列表，不包含数据量、记录数或任何统计信息。
    - 如果用户的问题涉及“数据量”、“记录数”、“最多/最少”等量化指标，**严禁使用此工具获取结果**，你应该自主编写 SQL 查询（如查询 `information_schema` 或具体表的 `COUNT(*)`）。
    - 传 filter_query: 根据业务问题语义进行 RAG 检索，返回语义最相关的几张表。
    - 不传 filter_query: 返回数据库内所有的表名。

    Args:
        filter_query: 可选。用于检索的用户问题关键词或业务术语。留空则返回所有表。
        top_k: 可选。使用检索时返回的表名数量上限（默认 5），仅代表展示数量，不代表某种排序权重。

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
    【防御性编程必需工具】获取指定表的详细结构信息（Schema）。
    在你准备动手写 SQL 之前，**必须**使用此工具确认表的字段名、数据类型以及可能的外键关联。
    如果上次执行 SQL 报了“字段不存在”的错误，你也应该再次调用此工具确认真正的字段名。
    该工具返回的内容包含 DDL 和有价值的中文注释，是你写出正确 SQL 的关键。

    Args:
        table_names: 需要确认结构的表名列表（如 ["Employee", "Customer"]）。

    Returns:
        str: 包含字段、类型、注释及外键定义的文本。
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
    【终极执行工具】执行你编写的 SELECT SQL 查询，并返回 Markdown 表格形式的数据结果。
    如果返回了报错信息（如 SQL 语法错误、未知字段等），请**不要马上放弃并回复用户**。
    你应该分析返回的错误信息，并在下一次思考中重新编写 SQL，或者使用 get_schema_tool 查阅结构后再次尝试。
    内部自动进行安全校验（sqlglot AST）和行数限制。

    Args:
        sql_query: 待执行的 SQL 查询

    Returns:
        str: Markdown 格式的结果或错误信息
    """
    logger.info(f"执行 SQL: {sql_query[:100]}...")
    return execute_query(sql_query)
