"""日志模块 - 使用滚动日志"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "feedland",
    log_dir: str = "output/logs",
    days: int = 3,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    配置滚动日志

    Args:
        name: logger 名称
        log_dir: 日志目录
        days: 保持日志的天数
        level: 日志级别
        console: 是否同时输出到控制台

    Returns:
        配置好的 logger
    """
    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 配置根 logger，捕获所有模块的日志
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 避免重复添加 handler
    if root_logger.handlers:
        return logging.getLogger(name)

    # 滚动日志：每天一个文件，保持 N 天
    log_file = f"{log_dir}/app.log"
    handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",      # 每天午夜滚动
        interval=1,          # 间隔 1 天
        backupCount=days,    # 保持 N 天
        encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"  # 文件名格式: app.log-2026-04-14

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # 同时输出到控制台
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return logging.getLogger(name)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger
    
    Args:
        name: logger 名称，如果是 None 则获取根 logger
    
    Returns:
        logger
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger("feedland")
