#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from loguru import logger

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件名格式
log_file_name = time.strftime("%Y-%m-%d") + ".log"
log_file_path = os.path.join(LOG_DIR, log_file_name)

# 日志级别
LOG_LEVEL = "DEBUG"

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 移除默认的日志处理器
logger.remove()

# 添加控制台输出
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# 添加文件输出
logger.add(
    log_file_path,
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    rotation="00:00",  # 每天零点创建新文件
    retention="7 days",  # 保留7天的日志
    compression="zip",  # 压缩历史日志
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)


def get_logger():
    """
    获取日志对象
    :return: logger对象
    """
    return logger


def setup_logger(level=None):
    """
    设置日志级别
    :param level: 日志级别
    :return: logger对象
    """
    if level:
        logger.configure(levels=[{"name": level, "no": logger.level(level).no}])
    return logger


# 导出全局日志对象
__all__ = ["logger", "get_logger", "setup_logger"] 