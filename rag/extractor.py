from sqlalchemy import inspect, create_engine, text
from config.settings import get_settings
from models.schemas import TableSchema, ColumnSchema
from loguru import logger
import importlib.util
import os
import sys

# Dynamic import for optional local config
def get_local_descriptions():
    try:
        # Add project root to sys.path to find config
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        from config.chinook_zh import schema_descriptions
        return schema_descriptions
    except ImportError:
        logger.warning("Local schema descriptions (config/chinook_zh.py) not found or failed to import.")
        return {}
    except Exception as e:
        logger.warning(f"Error loading local descriptions: {e}")
        return {}

class SchemaExtractor:
    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(settings.database_url)
        self.inspector = inspect(self.engine)
        self.local_descriptions = get_local_descriptions()

    def get_all_table_names(self) -> list[str]:
        return self.inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> TableSchema:
        columns = []
        try:
            inspector_columns = self.inspector.get_columns(table_name)
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            pks = pk_constraint.get('constrained_columns', [])
            fks = self.inspector.get_foreign_keys(table_name)
            
            # Map column name to foreign key target
            fk_map = {}
            for fk in fks:
                for loc_col, rem_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    fk_map[loc_col] = f"{fk['referred_table']}.{rem_col}"

            # Get local table description
            local_table_desc = self.local_descriptions.get(table_name, {})
            table_comment = self.inspector.get_table_comment(table_name).get('text')
            
            # Priority: DB Comment > Local Config
            final_table_desc = table_comment if table_comment else local_table_desc.get('description')

            for col in inspector_columns:
                col_name = col['name']
                # Get local column description
                local_col_desc = local_table_desc.get('columns', {}).get(col_name)
                db_col_comment = col.get('comment')
                
                # Priority: DB Comment > Local Config
                final_col_desc = db_col_comment if db_col_comment else local_col_desc

                columns.append(ColumnSchema(
                    name=col_name,
                    type=str(col['type']),
                    description=final_col_desc,
                    primary_key=col_name in pks,
                    foreign_key=fk_map.get(col_name)
                ))
            
            # Get Create Table DDL (MySQL specific)
            ddl = ""
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SHOW CREATE TABLE {table_name}"))
                    row = result.fetchone()
                    if row:
                        ddl = row[1]
            except Exception as e:
                logger.warning(f"Failed to get DDL for table {table_name}: {e}")

            return TableSchema(
                name=table_name,
                description=final_table_desc,
                columns=columns,
                ddl=ddl
            )
        except Exception as e:
            logger.error(f"Error extracting schema for {table_name}: {e}")
            raise

    def extract_all_schemas(self) -> list[TableSchema]:
        schemas = []
        for table in self.get_all_table_names():
            logger.info(f"Extracting schema for {table}...")
            schemas.append(self.get_table_schema(table))
        return schemas

schema_extractor = SchemaExtractor()
