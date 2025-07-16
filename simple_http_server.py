#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import http.server
import socketserver
import socket
import threading
import time


def start_simple_server(directory="reports", port=8081):
    """
    启动一个简单的HTTP服务器
    :param directory: 服务器根目录
    :param port: 服务器端口
    :return: 服务器URL
    """
    # 确保使用绝对路径
    directory = os.path.abspath(directory)
    print(f"服务器根目录: {directory}")
    
    # 确保目录存在
    if not os.path.exists(directory):
        print(f"目录不存在: {directory}")
        return None
    
    # 切换到目标目录
    original_dir = os.getcwd()
    os.chdir(directory)
    print(f"当前工作目录: {os.getcwd()}")
    print(f"目录内容: {os.listdir('.')}")
    
    # 创建处理器
    handler = http.server.SimpleHTTPRequestHandler
    
    # 创建服务器
    httpd = socketserver.TCPServer(("0.0.0.0", port), handler)
    
    # 获取本机IP地址
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    # 构建URL
    url = f"http://{ip_address}:{port}"
    
    # 启动服务器线程
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"简单HTTP服务器已启动: {url}")
    
    # 恢复工作目录
    os.chdir(original_dir)
    
    return url, httpd


if __name__ == "__main__":
    # 解析命令行参数
    directory = "reports"
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    port = 8081
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    # 启动服务器
    url, httpd = start_simple_server(directory, port)
    
    if url:
        print(f"服务器已启动: {url}")
        print("按Ctrl+C停止服务器")
        
        try:
            # 保持服务器运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            httpd.shutdown()
            httpd.server_close()
            print("服务器已停止")
    else:
        print("启动服务器失败")
        sys.exit(1) 