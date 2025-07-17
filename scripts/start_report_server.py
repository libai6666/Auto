#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.notification import start_report_server
from utils.logger import logger


def parse_args():
    """
    解析命令行参数
    :return: 解析结果
    """
    parser = argparse.ArgumentParser(description="测试报告服务器")
    
    # 服务器参数
    parser.add_argument("--dir", "-d", default="reports",
                        help="报告根目录")
    parser.add_argument("--port", "-p", type=int, default=7987,
                        help="服务器端口")
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 设置工作目录为项目根目录
    os.chdir(project_root)
    
    # 确保报告目录是绝对路径
    reports_dir = os.path.abspath(args.dir)
    
    # 日志记录
    logger.info("=" * 80)
    logger.info("启动测试报告服务器")
    logger.info(f"工作目录: {project_root}")
    logger.info(f"报告目录: {reports_dir}")
    logger.info(f"服务器端口: {args.port}")
    
    # 启动报告服务器
    url = start_report_server(reports_dir, args.port)
    if url:
        logger.info(f"报告服务器已启动: {url}")
        logger.info("访问报告列表: " + url)
        logger.info("按Ctrl+C停止服务器")
        
        try:
            # 保持服务器运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("正在停止服务器...")
            from utils.notification import stop_report_server
            stop_report_server()
            logger.info("服务器已停止")
    else:
        logger.error("启动报告服务器失败")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 