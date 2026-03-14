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
    mysql_password: str
    mysql_db: str = "sql_rag_db"

    # ChromaDB Configuration
    chroma_db_dir: str = "data/chromadb_store"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    session_ttl: int = 1800  # 会话过期时间（秒），默认 30 分钟
    max_history_rounds: int = 5  # 最大保留对话轮数
    
    # Auth & JWT Configuration
    secret_key: str = "60e9095699478f79f6f69f8999a0956d9876543210abcdef" # 建议从环境变量读取
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30  # 默认 30 天

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"

@lru_cache()
def get_settings():
    return Settings()
