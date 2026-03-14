import sys
import os

# 将项目根目录添加到 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.engine import engine
from db.models import Base
from loguru import logger

def init_db():
    try:
        logger.info("正在初始化 Auth 与历史记录相关表...")
        Base.metadata.create_all(bind=engine)
        logger.success("数据库表初始化成功！")
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
