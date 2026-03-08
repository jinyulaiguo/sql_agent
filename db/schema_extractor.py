"""Schema 提取器模块

通过 SQLAlchemy Inspector 从 MySQL 提取表结构信息，
并结合本地中文注释配置增强语义描述。
"""

from sqlalchemy import text
from db.engine import engine, inspector
from models.schemas import TableSchema, ColumnSchema
from exceptions import SchemaExtractionError
from loguru import logger


def _load_local_descriptions() -> dict:
    """加载本地中文字段描述配置（可选）"""
    try:
        from data.chinook_zh import schema_descriptions
        return schema_descriptions
    except ImportError:
        logger.warning("未找到本地 Schema 描述文件 (data/chinook_zh.py)，将仅使用数据库注释。")
        return {}
    except Exception as e:
        logger.warning(f"加载本地描述失败: {e}")
        return {}


class SchemaExtractor:
    """数据库 Schema 提取器"""

    def __init__(self):
        self.local_descriptions = _load_local_descriptions()

    def get_all_table_names(self) -> list[str]:
        """获取数据库中所有表名"""
        return inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> TableSchema:
        """
        获取指定表的详细 Schema 信息。

        Args:
            table_name: 表名

        Returns:
            TableSchema: 包含字段、主键、外键、DDL 等完整信息

        Raises:
            SchemaExtractionError: 提取失败时抛出
        """
        try:
            inspector_columns = inspector.get_columns(table_name)
            pk_constraint = inspector.get_pk_constraint(table_name)
            pks = pk_constraint.get("constrained_columns", [])
            fks = inspector.get_foreign_keys(table_name)

            # 构建外键映射: 本地字段 -> 引用表.引用字段
            fk_map = {}
            for fk in fks:
                for loc_col, rem_col in zip(
                    fk["constrained_columns"], fk["referred_columns"]
                ):
                    fk_map[loc_col] = f"{fk['referred_table']}.{rem_col}"

            # 获取本地表级描述
            local_table_desc = self.local_descriptions.get(table_name, {})
            table_comment = inspector.get_table_comment(table_name).get("text")
            # 优先级: 数据库注释 > 本地配置
            final_table_desc = table_comment or local_table_desc.get("description")

            # 构建字段列表
            columns = []
            for col in inspector_columns:
                col_name = col["name"]
                local_col_desc = local_table_desc.get("columns", {}).get(col_name)
                db_col_comment = col.get("comment")
                # 优先级: 数据库注释 > 本地配置
                final_col_desc = db_col_comment or local_col_desc

                columns.append(
                    ColumnSchema(
                        name=col_name,
                        type=str(col["type"]),
                        description=final_col_desc,
                        primary_key=col_name in pks,
                        foreign_key=fk_map.get(col_name),
                    )
                )

            # 获取建表 DDL (MySQL)
            ddl = ""
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SHOW CREATE TABLE `{table_name}`"))
                    row = result.fetchone()
                    if row:
                        ddl = row[1]
            except Exception as e:
                logger.warning(f"获取表 {table_name} 的 DDL 失败: {e}")

            return TableSchema(
                name=table_name,
                description=final_table_desc,
                columns=columns,
                ddl=ddl,
            )
        except Exception as e:
            logger.error(f"提取表 {table_name} 的 Schema 失败: {e}")
            raise SchemaExtractionError(f"提取表 {table_name} 的 Schema 失败: {e}")

    def extract_all_schemas(self) -> list[TableSchema]:
        """提取数据库中所有表的 Schema"""
        schemas = []
        for table in self.get_all_table_names():
            logger.info(f"正在提取 {table} 的 Schema...")
            schemas.append(self.get_table_schema(table))
        return schemas


# 模块级单例
schema_extractor = SchemaExtractor()
