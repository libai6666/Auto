#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import yaml
from datetime import datetime, timedelta
from loguru import logger

# 默认配置
DEFAULT_LOGS_RETENTION_DAYS = 7

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


def load_config():
    """
    加载配置文件
    :return: 配置字典
    """
    config_path = os.path.join(PROJECT_ROOT, "config", "config.yaml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}


def cleanup_logs():
    """
    清理旧的日志文件
    根据配置保留最近N天的日志，删除更早的日志
    """
    # 加载配置
    config = load_config()
    cleanup_config = config.get('cleanup', {})
    
    # 检查是否启用清理
    if not cleanup_config.get('enabled', True):
        logger.info("文件自动清理功能已禁用")
        return
    
    # 获取保留天数
    retention_days = cleanup_config.get('logs_retention_days', DEFAULT_LOGS_RETENTION_DAYS)
    
    if not os.path.exists(LOG_DIR):
        return
    
    # 获取当前日期
    now = datetime.now()
    cutoff_date = now - timedelta(days=retention_days)
    
    logger.info(f"开始清理日志文件，保留最近{retention_days}天的日志...")
    
    # 用于匹配日志文件名称中的日期的正则表达式
    # 匹配格式如: 2025-04-24.log
    pattern = r'(\d{4}-\d{2}-\d{2})\.log'
    
    removed_count = 0
    
    # 遍历logs目录下的所有文件
    for item in os.listdir(LOG_DIR):
        item_path = os.path.join(LOG_DIR, item)
        
        # 检查是否是日志文件
        if os.path.isfile(item_path) and item.endswith('.log'):
            match = re.search(pattern, item)
            if match:
                # 提取日期
                date_str = match.group(1)
                try:
                    # 解析日期
                    item_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # 检查是否超过保留期限
                    if item_date < cutoff_date.date():
                        logger.debug(f"删除过期日志文件: {item_path}")
                        os.remove(item_path)
                        removed_count += 1
                except ValueError:
                    logger.warning(f"无法解析日志文件的日期: {item}")
        
        # 检查是否是压缩后的日志文件（zip格式）
        elif os.path.isfile(item_path) and item.endswith('.zip'):
            # 尝试从文件名中提取日期
            zip_match = re.search(r'(\d{4}-\d{2}-\d{2})\.log\.zip', item)
            if zip_match:
                date_str = zip_match.group(1)
                try:
                    item_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if item_date < cutoff_date.date():
                        logger.debug(f"删除过期压缩日志文件: {item_path}")
                        os.remove(item_path)
                        removed_count += 1
                except ValueError:
                    logger.warning(f"无法解析压缩日志文件的日期: {item}")
    
    logger.info(f"日志清理完成，共删除了 {removed_count} 个过期日志文件")


# 导出全局日志对象
__all__ = ["logger", "get_logger", "setup_logger", "cleanup_logs"] 