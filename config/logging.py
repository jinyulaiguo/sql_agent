"""日志配置模块

统一配置 loguru 日志格式和输出。
"""

import sys
from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """
    配置全局日志。

    Args:
        level: 日志级别，默认 INFO
    """
    # 移除默认 handler
    logger.remove()

    # 终端输出：彩色格式
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
    )
