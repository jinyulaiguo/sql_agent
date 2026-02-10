from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from config.settings import get_settings
from loguru import logger
import pandas as pd

settings = get_settings()

class DBTools:
    def __init__(self):
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def list_tables(self) -> list[str]:
        """List all tables in the database."""
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> str:
        """Get the schema definition for a specific table."""
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        # Simplify schema representation for LLM
        schema_info = f"Table: {table_name}\nColumns:\n"
        for col in columns:
            schema_info += f"- {col['name']} ({col['type']}): {col.get('comment', '')}\n"
        return schema_info

    def execute_sql(self, sql_query: str) -> str:
        """Execute a SQL query and return the results as a string."""
        if not sql_query.strip().lower().startswith("select"):
             return "Error: Only SELECT queries are allowed."

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df.to_markdown(index=False)
        except Exception as e:
            logger.error(f"SQL Execution Error: {e}")
            return f"Error executing SQL: {str(e)}"

db_tools = DBTools()
