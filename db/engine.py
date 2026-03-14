"""统一的 SQLAlchemy Engine 管理模块

全局只维护一个 Engine 实例和一个 Inspector 实例，
所有需要数据库访问的模块统一从此处导入。
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

inspector = inspect(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
