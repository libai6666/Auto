#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
from utils.logger import logger


def get_local_ip():
    """
    获取本机局域网IP地址
    :return: IP地址字符串
    """
    # 优先从环境变量获取（Docker环境）
    env_host = os.environ.get("REPORT_SERVER_HOST")
    if env_host:
        logger.info(f"从环境变量获取IP: {env_host}")
        return env_host
    
    try:
        # 创建UDP socket，连接到外部地址来获取本机IP
        # 不需要真正发送数据，只是为了获取路由信息
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"自动检测到局域网IP: {local_ip}")
        return local_ip
    except Exception as e:
        logger.warning(f"自动检测IP失败: {str(e)}")
        
        # 降级方案：使用hostname获取
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            logger.info(f"通过hostname获取IP: {local_ip}")
            return local_ip
        except Exception as e2:
            logger.error(f"获取IP失败: {str(e2)}")
            return "localhost"


def get_report_server_url(port=7987):
    """
    获取报告服务器完整URL
    :param port: 服务器端口
    :return: 完整的URL，如 http://192.168.0.105:7987
    """
    ip = get_local_ip()
    url = f"http://{ip}:{port}"
    logger.debug(f"报告服务器URL: {url}")
    return url


if __name__ == "__main__":
    # 测试代码
    print(f"本机IP: {get_local_ip()}")
    print(f"报告服务器URL: {get_report_server_url()}")

