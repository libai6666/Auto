#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import threading
import time
import json
import shutil
import glob
import http.server
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from utils.logger import logger


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    多线程HTTP服务器
    """
    daemon_threads = True
    allow_reuse_address = True


class ReportHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    报告HTTP请求处理器
    """
    def __init__(self, *args, directory=None, **kwargs):
        # 确保设置了directory参数
        if directory is None:
            directory = os.getcwd()
        self.directory = os.path.abspath(directory)
        logger.debug(f"初始化处理器，目录: {self.directory}")
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def log_message(self, format, *args):
        """
        重写日志方法，使用项目的logger
        """
        logger.debug(f"报告服务器: {format % args}")
    
    def do_GET(self):
        """
        处理GET请求
        """
        logger.debug(f"接收到GET请求: {self.path}")
        logger.debug(f"当前工作目录: {os.getcwd()}")
        logger.debug(f"服务器根目录: {self.directory}")
        
        # 规范化路径
        path = self.path.strip('/')
        logger.debug(f"规范化后的路径: {path}")
        
        # 如果路径为空，显示根目录
        if not path:
            logger.debug("请求根目录")
            return self.list_directory(self.directory)
        
        # 检查路径是否是目录根
        parts = path.split('/')
        first_part = parts[0]
        
        # 检查是否是报告目录
        report_dir = os.path.join(self.directory, first_part)
        logger.debug(f"检查是否是报告目录: {report_dir}")
        
        if os.path.isdir(report_dir):
            logger.debug(f"找到报告目录: {report_dir}")
            
            # 如果请求只有报告ID，重定向到index.html
            if len(parts) == 1:
                logger.debug(f"重定向到index.html: /{first_part}/index.html")
                self.send_response(301)
                self.send_header("Location", f"/{first_part}/index.html")
                self.end_headers()
                return
        
        # 构建物理路径
        physical_path = os.path.join(self.directory, path)
        logger.debug(f"物理路径: {physical_path}")
        
        # 检查路径是否存在
        if not os.path.exists(physical_path):
            logger.debug(f"路径不存在: {physical_path}")
            # 尝试列出父目录内容，帮助调试
            parent_dir = os.path.dirname(physical_path)
            if os.path.exists(parent_dir):
                logger.debug(f"父目录存在: {parent_dir}")
                logger.debug(f"父目录内容: {os.listdir(parent_dir)}")
            self.send_error(404, "File not found")
            return
        
        # 如果是目录
        if os.path.isdir(physical_path):
            logger.debug(f"请求的是目录: {physical_path}")
            logger.debug(f"目录内容: {os.listdir(physical_path)}")
            
            # 检查是否有index.html
            index_path = os.path.join(physical_path, "index.html")
            if os.path.exists(index_path):
                logger.debug(f"找到index.html: {index_path}")
                return self.serve_file(index_path)
            
            # 否则列出目录内容
            return self.list_directory(physical_path)
        
        # 如果是文件，直接提供
        logger.debug(f"请求的是文件: {physical_path}")
        return self.serve_file(physical_path)
    
    def serve_file(self, path):
        """
        提供文件
        """
        try:
            logger.debug(f"提供文件: {path}")
            
            # 确定文件类型
            ctype = self.guess_type(path)
            
            # 打开文件
            with open(path, 'rb') as f:
                content = f.read()
            
            # 发送响应
            self.send_response(200)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
            return True
        
        except Exception as e:
            logger.error(f"提供文件出错: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")
            return False
    
    def list_directory(self, path):
        """
        列出目录内容
        """
        try:
            logger.debug(f"列出目录内容: {path}")
            
            # 获取目录内容
            list = os.listdir(path)
            list.sort(key=lambda a: a.lower())
            
            # 构建HTML
            r = []
            r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
            r.append('<html>\n<head>')
            r.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            r.append(f'<title>Directory listing for {self.path}</title>\n</head>')
            r.append('<body>\n<h1>Directory listing for {}</h1>'.format(self.path))
            r.append('<hr>\n<ul>')
            
            # 添加上级目录链接
            if self.path != '/':
                r.append('<li><a href="..">Parent Directory</a></li>')
            
            # 添加目录内容
            for name in list:
                fullname = os.path.join(path, name)
                displayname = name
                linkname = name
                
                # 添加斜杠表示目录
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                
                r.append('<li><a href="{}">{}</a></li>'.format(linkname, displayname))
            
            r.append('</ul>\n<hr>\n</body>\n</html>\n')
            
            # 合并HTML
            content = '\n'.join(r).encode('utf-8')
            
            # 发送响应
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
            return True
        
        except Exception as e:
            logger.error(f"列出目录内容出错: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")
            return False


class ReportServer:
    """
    报告服务器，用于长期托管Allure报告
    """
    def __init__(self, reports_dir="reports", port=7987):
        """
        初始化报告服务器
        :param reports_dir: 报告根目录
        :param port: 服务器端口
        """
        self.reports_dir = os.path.abspath(reports_dir)
        self.port = port
        self.server = None
        self.server_thread = None
        self.url = None
        self.reports_index = {}
        
        # 确保报告目录存在
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 创建索引文件路径
        self.index_file = os.path.join(self.reports_dir, "reports_index.json")
        
        # 加载报告索引
        self._load_index()
    
    def _load_index(self):
        """
        加载报告索引
        """
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.reports_index = json.load(f)
                logger.info(f"已加载报告索引，共 {len(self.reports_index)} 个报告")
            except Exception as e:
                logger.error(f"加载报告索引失败: {str(e)}")
                self.reports_index = {}
        else:
            self.reports_index = {}
    
    def _save_index(self):
        """
        保存报告索引
        """
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.reports_index, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存报告索引，共 {len(self.reports_index)} 个报告")
        except Exception as e:
            logger.error(f"保存报告索引失败: {str(e)}")
    
    def add_report(self, report_id, report_dir, metadata=None):
        """
        添加报告到索引
        :param report_id: 报告ID
        :param report_dir: 报告目录
        :param metadata: 报告元数据
        :return: 报告URL
        """
        if not metadata:
            metadata = {}
        
        # 构建报告目标目录
        target_dir = os.path.join(self.reports_dir, report_id)
        logger.debug(f"报告目标目录: {target_dir}")
        
        # 如果目标目录已存在，先删除
        if os.path.exists(target_dir):
            logger.debug(f"目标目录已存在，删除: {target_dir}")
            shutil.rmtree(target_dir)
        
        # 复制报告文件
        try:
            # 确保源目录存在
            if not os.path.exists(report_dir):
                logger.error(f"源报告目录不存在: {report_dir}")
                return None
            
            # 检查源目录中是否有index.html
            if not os.path.exists(os.path.join(report_dir, "index.html")):
                logger.error(f"源报告目录中没有index.html: {report_dir}")
                return None
            
            logger.debug(f"源目录内容: {os.listdir(report_dir)}")
            
            # 复制目录
            shutil.copytree(report_dir, target_dir)
            logger.info(f"已复制报告文件到 {target_dir}")
            
            # 检查复制后的目录是否存在
            if not os.path.exists(target_dir):
                logger.error(f"复制后的目录不存在: {target_dir}")
                return None
            
            # 检查复制后的index.html是否存在
            if not os.path.exists(os.path.join(target_dir, "index.html")):
                logger.error(f"复制后的目录中没有index.html: {target_dir}")
                return None
            
            logger.debug(f"复制后的目录内容: {os.listdir(target_dir)}")
            logger.debug(f"报告目录完整路径: {os.path.abspath(target_dir)}")
        except Exception as e:
            logger.error(f"复制报告文件失败: {str(e)}")
            return None
        
        # 更新索引
        report_url = f"{self.url}/{report_id}" if self.url else None
        self.reports_index[report_id] = {
            "id": report_id,
            "path": target_dir,
            "url": report_url,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata
        }
        
        # 保存索引
        self._save_index()
        
        return report_url
    
    def generate_index_html(self):
        """
        生成索引HTML页面
        """
        index_html = os.path.join(self.reports_dir, "index.html")
        
        try:
            with open(index_html, 'w', encoding='utf-8') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>测试报告列表</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f8f8;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .badge {
            display: inline-block;
            padding: 3px 7px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .badge-success {
            background-color: #28a745;
        }
        .badge-warning {
            background-color: #ffc107;
            color: #212529;
        }
        .badge-danger {
            background-color: #dc3545;
        }
        .refresh {
            float: right;
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        .refresh:hover {
            background-color: #0052a3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告列表 <button class="refresh" onclick="location.reload()">刷新</button></h1>
        <table>
            <thead>
                <tr>
                    <th>报告ID</th>
                    <th>创建时间</th>
                    <th>测试环境</th>
                    <th>通过率</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
""")
                
                # 按创建时间倒序排序
                sorted_reports = sorted(
                    self.reports_index.values(),
                    key=lambda x: x.get("created_at", ""),
                    reverse=True
                )
                
                for report in sorted_reports:
                    report_id = report.get("id", "")
                    created_at = report.get("created_at", "")
                    metadata = report.get("metadata", {})
                    env = metadata.get("env", "未知")
                    
                    # 计算通过率
                    total = metadata.get("total", 0)
                    passed = metadata.get("passed", 0)
                    pass_rate = f"{(passed / total * 100):.2f}%" if total > 0 else "0.00%"
                    
                    # 确定通过率徽章颜色
                    badge_class = "badge-success"
                    if total == 0 or passed / total < 0.7:
                        badge_class = "badge-danger"
                    elif passed / total < 0.9:
                        badge_class = "badge-warning"
                    
                    f.write(f"""
                <tr>
                    <td>{report_id}</td>
                    <td>{created_at}</td>
                    <td>{env}</td>
                    <td><span class="badge {badge_class}">{pass_rate}</span></td>
                    <td><a href="{report_id}/index.html" target="_blank">查看报告</a></td>
                </tr>
""")
                
                f.write("""
            </tbody>
        </table>
    </div>
</body>
</html>
""")
            
            logger.info(f"已生成索引HTML页面: {index_html}")
        except Exception as e:
            logger.error(f"生成索引HTML页面失败: {str(e)}")
    
    def start(self):
        """
        启动HTTP服务器
        :return: 服务器URL
        """
        if self.server:
            logger.warning("报告服务器已经在运行")
            return self.url
        
        # 生成索引HTML
        self.generate_index_html()
        
        # 打印当前工作目录和目录内容
        logger.debug(f"当前工作目录: {os.getcwd()}")
        logger.debug(f"报告目录: {self.reports_dir}")
        logger.debug(f"目录内容: {os.listdir(self.reports_dir)}")
        
        # 尝试启动服务器
        try:
            # 保存原始工作目录
            original_dir = os.getcwd()
            
            # 创建处理器，使用自定义的ReportHTTPRequestHandler
            handler = lambda *args, **kwargs: ReportHTTPRequestHandler(*args, directory=self.reports_dir, **kwargs)
            
            # 创建服务器
            self.server = ThreadedHTTPServer(('0.0.0.0', self.port), handler)
            
            # 获取实际端口
            self.port = self.server.server_port
            
            # Docker 环境中获取IP地址
            ip_address = None
            
            # 优先尝试获取环境变量中的主机名
            host_env = os.environ.get("REPORT_SERVER_HOST")
            if host_env:
                ip_address = host_env
                logger.info(f"从环境变量获取主机名: {ip_address}")
            else:
                try:
                    # 尝试获取真实的外部IP地址
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip_address = s.getsockname()[0]
                    s.close()
                except Exception as e:
                    logger.warning(f"获取真实IP地址失败: {str(e)}")
                    # 在Docker环境中使用0.0.0.0
                    ip_address = socket.gethostbyname(socket.gethostname())
            
            # 构建URL
            self.url = f"http://{ip_address}:{self.port}"
            
            # 输出提示信息，方便用户了解多个访问地址
            logger.info(f"报告可通过以下URL访问：")
            logger.info(f"- 本机访问: http://localhost:{self.port}")
            logger.info(f"- 服务器访问: http://{ip_address}:{self.port}")
            # 特别提示Docker环境
            if os.environ.get("DOCKER_ENV"):
                logger.info(f"- 注意: 在Docker环境中运行，请使用宿主机IP访问")
            
            # 更新报告URL
            for report_id, report in self.reports_index.items():
                report["url"] = f"{self.url}/{report_id}"
            
            # 保存索引
            self._save_index()
            
            # 启动服务器线程
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"报告服务器已启动: {self.url}")
            
            return self.url
        
        except Exception as e:
            logger.error(f"启动报告服务器失败: {str(e)}")
            
            # 如果已经切换了工作目录，恢复
            if 'original_dir' in locals():
                os.chdir(original_dir)
            
            return None
    
    def stop(self):
        """
        停止HTTP服务器
        """
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                logger.info("报告服务器已停止")
            except Exception as e:
                logger.error(f"停止报告服务器失败: {str(e)}")
            finally:
                self.server = None
                self.server_thread = None
                self.url = None


# 全局服务器实例
_report_server = None


def get_report_server(reports_dir="reports", port=7987):
    """
    获取报告服务器实例
    :param reports_dir: 报告根目录
    :param port: 服务器端口
    :return: 报告服务器实例
    """
    global _report_server
    
    if not _report_server:
        _report_server = ReportServer(reports_dir, port)
    
    return _report_server


def start_report_server(reports_dir="reports", port=7987):
    """
    启动报告服务器
    :param reports_dir: 报告根目录
    :param port: 服务器端口
    :return: 服务器URL
    """
    # 确保使用绝对路径
    reports_dir = os.path.abspath(reports_dir)
    logger.debug(f"报告服务器根目录: {reports_dir}")
    
    # 确保目录存在
    os.makedirs(reports_dir, exist_ok=True)
    
    server = get_report_server(reports_dir, port)
    return server.start()


def add_report(report_id, report_dir, metadata=None):
    """
    添加报告
    :param report_id: 报告ID
    :param report_dir: 报告目录
    :param metadata: 报告元数据
    :return: 报告URL
    """
    # 从配置中获取报告服务器URL
    from utils.logger import logger
    import yaml
    import os
    import shutil
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "config.yaml")
    report_server_url = None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            report_server = config.get('report_server', {})
            report_server_url = report_server.get('url')
            is_enabled = report_server.get('enabled', True)
            
            if not is_enabled:
                logger.info("报告服务器功能已禁用")
                return None
            
            if not report_server_url:
                # 如果配置中没有URL，尝试使用本地服务器
                server = get_report_server()
                if not server.url:
                    server.start()
                return server.add_report(report_id, report_dir, metadata)
    except Exception as e:
        logger.error(f"读取配置失败: {str(e)}")
        # 如果读取配置失败，尝试使用本地服务器
        server = get_report_server()
        if not server.url:
            server.start()
        return server.add_report(report_id, report_dir, metadata)
    
    # 解析服务器地址和端口
    import re
    match = re.match(r"http://(.*):(\d+)", report_server_url)
    if not match:
        logger.error(f"无效的服务器URL格式: {report_server_url}")
        return None
    
    server_host, server_port = match.groups()
    server_port = int(server_port)
    
    # 构建目标路径
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports", report_id)
    
    # 复制报告文件
    try:
        # 如果目标目录已存在，先删除
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # 复制目录
        shutil.copytree(report_dir, target_dir)
        logger.info(f"已复制报告文件到 {target_dir}")
    except Exception as e:
        logger.error(f"复制报告文件失败: {str(e)}")
        return None
    
    # 构建报告URL
    report_url = f"{report_server_url}/{report_id}"
    logger.info(f"报告已准备就绪，可通过以下URL访问: {report_url}")
    
    return report_url


def stop_report_server():
    """
    停止报告服务器
    """
    global _report_server
    if _report_server:
        _report_server.stop()
        _report_server = None


if __name__ == "__main__":
    # 添加命令行参数支持
    import argparse
    
    parser = argparse.ArgumentParser(description="测试报告服务器")
    parser.add_argument("--dir", "-d", default="reports", help="报告根目录")
    parser.add_argument("--port", "-p", type=int, default=7987, help="服务器端口")
    args = parser.parse_args()
    
    # 启动报告服务器
    reports_dir = args.dir
    port = args.port
    
    url = start_report_server(reports_dir, port)
    print(f"报告服务器已启动: {url}")
    print("按Ctrl+C停止服务器")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_report_server()
        print("报告服务器已停止") 