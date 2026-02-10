from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # DeepSeek / OpenAI API Configuration
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    model_name: str = "deepseek-chat"

    # MySQL Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "rag_user"
    mysql_password: str = "ragAgent2026"
    mysql_db: str = "sql_rag_db"

    # ChromaDB Configuration
    chroma_db_dir: str = "data/chromadb_store"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"

@lru_cache()
def get_settings():
    return Settings()
