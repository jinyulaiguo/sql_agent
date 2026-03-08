"""SQL 安全校验模块

使用 sqlglot 将 SQL 解析为 AST，实施严格的安全准入检查。
仅允许 SELECT 查询，拦截所有写操作。
"""

import sqlglot
from exceptions import SQLValidationError
from loguru import logger


def validate_sql(sql_query: str) -> None:
    """
    校验 SQL 是否为安全的 SELECT 查询。

    Args:
        sql_query: 待校验的 SQL 字符串

    Raises:
        SQLValidationError: 当 SQL 不合法或非 SELECT 操作时抛出
    """
    try:
        parsed = sqlglot.parse_one(sql_query)
    except sqlglot.errors.ParseError as e:
        logger.warning(f"SQL 语法解析失败: {e}")
        raise SQLValidationError(f"SQL 语法错误: {e}。请检查 SQL 拼写。")

    # 严格限制：只允许 SELECT
    if not isinstance(parsed, sqlglot.exp.Select):
        raise SQLValidationError(
            "为确保安全，只允许执行 SELECT 查询。"
            "禁止 DROP、DELETE、UPDATE、INSERT 等操作。"
        )

    logger.debug(f"SQL 安全校验通过: {sql_query[:80]}...")
