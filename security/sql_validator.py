"""SQL 安全校验模块

使用 sqlglot 将 SQL 解析为 AST，实施严格的安全准入检查。
仅允许 SELECT 查询，拦截所有写操作。
"""

import sqlglot
from sqlglot import exp
from exceptions import SQLValidationError
from loguru import logger


def validate_sql(sql_query: str) -> None:
    """
    校验 SQL 是否为安全的只读查询。
    支持 SELECT, UNION, WITH (CTE), SHOW, DESCRIBE, EXPLAIN。
    通过递归扫描 AST 拦截任何形式的修改操作（INSERT, UPDATE, DELETE, DROP 等）。

    Args:
        sql_query: 待校验的 SQL 字符串
    """
    try:
        parsed_list = sqlglot.parse(sql_query, read="mysql")
        if not parsed_list:
            raise SQLValidationError("无法解析 SQL。")
        # 仅取第一条语句（目前不鼓励多语句执行，且 executor 也是单语句模型）
        parsed = parsed_list[0]
    except sqlglot.errors.ParseError as e:
        logger.warning(f"SQL 语法解析失败: {e}")
        raise SQLValidationError(f"SQL 语法错误: {e}。请检查 SQL 拼写。")

    # 1. 顶层语句白名单
    allowed_types = (
        exp.Select,
        exp.Union,
        exp.Show,
        exp.Describe,
        exp.Query,  # 覆盖 Subquery, CTEs 等
    )
    
    if not isinstance(parsed, allowed_types):
        logger.warning(f"由于操作类型 {type(parsed)} 被拦截: {sql_query[:50]}...")
        raise SQLValidationError(
            "为确保安全，只允许执行只读查询（SELECT, UNION, WITH 等）。"
            "禁止数据修改或结构定义操作。"
        )

    # 2. 全树扫描黑名单 (防止嵌套或绕过)
    forbidden_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.Set,     # 防止修改会话变量
        exp.Command, # 防止原生指令绕过
    )

    for node in parsed.find_all(forbidden_types):
        logger.warning(f"检测到非法操作节点 {type(node)}: {sql_query[:50]}...")
        raise SQLValidationError(f"检测到非法操作: {type(node).__name__}，出于安全原因已被拦截。")

    logger.debug(f"SQL 安全校验通过: {sql_query[:80]}...")
