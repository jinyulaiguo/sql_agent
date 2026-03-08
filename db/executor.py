"""SQL 执行器模块

负责执行经过安全校验的 SQL 查询，并将结果格式化为 Markdown 表格。
"""

from sqlalchemy import text
from db.engine import engine
from security.sql_validator import validate_sql
from exceptions import SQLValidationError, DatabaseExecutionError
from loguru import logger
import pandas as pd


def execute_query(sql_query: str, max_rows: int = 20) -> str:
    """
    安全执行 SQL 查询并返回 Markdown 格式结果。

    流程：sqlglot AST 校验 → 执行 → 截断 → Markdown 格式化

    Args:
        sql_query: 待执行的 SQL 查询
        max_rows: 最大返回行数，默认 20

    Returns:
        str: Markdown 格式的查询结果，或错误/空结果提示

    Note:
        安全校验失败和执行错误都会返回友好的错误字符串（而非抛异常），
        因为这些字符串会作为 tool result 回传给 LLM 用于推理纠错。
    """
    # 1. 安全校验
    try:
        validate_sql(sql_query)
    except SQLValidationError as e:
        return f"错误: {e}"

    # 2. 执行查询
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchmany(max_rows)

            if not rows:
                return "未找到结果。"

            df = pd.DataFrame(rows, columns=result.keys())
            return df.to_markdown(index=False)
    except Exception as e:
        logger.error(f"SQL 执行错误: {e}")
        return f"数据库错误: {str(e)}。请检查表名和字段名是否存在。"
