"""Text-to-SQL Agent 自定义异常模块"""


class TextToSQLError(Exception):
    """Text-to-SQL Agent 基础异常"""
    pass


class SQLValidationError(TextToSQLError):
    """SQL 安全校验失败时抛出"""
    pass


class SchemaExtractionError(TextToSQLError):
    """Schema 提取失败时抛出"""
    pass


class DatabaseExecutionError(TextToSQLError):
    """数据库执行失败时抛出"""
    pass


class RAGRetrievalError(TextToSQLError):
    """RAG 检索失败时抛出"""
    pass
