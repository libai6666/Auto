#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logger import logger
import time
import os
from utils.data_handler import load_config
import allure  # 添加allure导入

class APIClient:
    """
    API客户端，封装了请求方法
    """
    def __init__(self, base_url=None, timeout=None):
        """
        初始化API客户端
        :param base_url: API基础URL
        :param timeout: 超时时间
        """
        config = load_config()
        
        # 获取当前环境配置
        current_env = config.get("current_env", "test")
        env_config = config.get("env_config", {}).get(current_env, {})
        
        # 设置基础URL和超时时间
        self.base_url = base_url or env_config.get("base_url", "")
        self.timeout = timeout or env_config.get("timeout", 10)
        
        # 创建会话
        self.session = requests.Session()
        
        # 重试配置
        retry_config = config.get("request", {})
        retries = retry_config.get("max_retries", 3)
        retry_delay = retry_config.get("retry_delay", 1)
        
        # 设置重试策略
        retry_strategy = Retry(
            total=retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "POST", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # 添加适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置请求头
        default_headers = config.get("request", {}).get("headers", {})
        self.session.headers.update(default_headers)
        
        # 设置是否验证SSL
        self.verify_ssl = config.get("request", {}).get("verify_ssl", True)
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, **kwargs):
        """
        发送HTTP请求
        :param method: 请求方法，如GET, POST, PUT, DELETE等
        :param url: 请求URL，如果不是完整URL，会自动添加base_url
        :param params: URL参数
        :param data: 请求数据
        :param json: JSON请求数据
        :param headers: 请求头
        :param files: 上传文件
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        method = method.upper()
        
        # 处理URL
        if not url.startswith(('http://', 'https://')):
            complete_url = f"{self.base_url}{url}"
        else:
            complete_url = url
        
        # 请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        log_msg = f"\n==================== REQUEST ====================\n"
        log_msg += f"Method: {method}\n"
        log_msg += f"URL: {complete_url}\n"
        
        # 记录请求头
        if headers:
            log_msg += "Headers:\n"
            for key, value in headers.items():
                # 敏感信息处理
                if key.lower() in ['authorization', 'token', 'password', 'secret']:
                    log_msg += f"  {key}: ******\n"
                else:
                    log_msg += f"  {key}: {value}\n"
        
        # 记录请求参数
        if params:
            import json as json_module  # 确保使用正确导入的 json 模块
            log_msg += f"Params: {json_module.dumps(params, ensure_ascii=False, indent=2)}\n"
        
        # 记录请求数据
        if data:
            import json as json_module  # 确保使用正确导入的 json 模块
            log_msg += f"Data: {json_module.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else data}\n"
        
        # 记录请求JSON
        if json:
            import json as json_module  # 确保使用正确导入的 json 模块
            log_msg += f"JSON: {json_module.dumps(json, ensure_ascii=False, indent=2)}\n"
        
        logger.info(log_msg)
        
        # 添加到Allure报告
        with allure.step(f"API请求: {method} {url}"):
            allure.attach(
                log_msg,
                name="请求详情",
                attachment_type=allure.attachment_type.TEXT
            )
            
        # 发送请求
        try:
            response = self.session.request(
                method=method,
                url=complete_url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                files=files,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            
            # 请求结束时间
            end_time = time.time()
            
            # 记录响应信息
            log_msg = f"\n==================== RESPONSE ===================\n"
            log_msg += f"Status Code: {response.status_code}\n"
            log_msg += f"Time Taken: {end_time - start_time:.2f}s\n"
            
            # 记录响应头
            log_msg += "Headers:\n"
            for key, value in response.headers.items():
                log_msg += f"  {key}: {value}\n"
            
            # 记录响应体
            try:
                import json as json_module  # 确保使用正确导入的 json 模块
                log_msg += f"Response Body: {json_module.dumps(response.json(), ensure_ascii=False, indent=2)}\n"
            except:
                log_msg += f"Response Body: {response.text}\n"
            
            logger.info(log_msg)
            
            # 添加到Allure报告
            with allure.step(f"API响应: HTTP {response.status_code}"):
                allure.attach(
                    log_msg,
                    name="响应详情",
                    attachment_type=allure.attachment_type.TEXT
                )
            
            return response
        
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            # 添加到Allure报告
            with allure.step("API请求异常"):
                allure.attach(
                    str(e),
                    name="异常信息",
                    attachment_type=allure.attachment_type.TEXT
                )
            raise
    
    def get(self, url, params=None, **kwargs):
        """
        发送GET请求
        :param url: 请求URL
        :param params: 请求参数
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        return self.request("GET", url, params=params, **kwargs)
    
    def post(self, url, data=None, json=None, **kwargs):
        """
        发送POST请求
        :param url: 请求URL
        :param data: 请求数据
        :param json: JSON请求数据
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        return self.request("POST", url, data=data, json=json, **kwargs)
    
    def put(self, url, data=None, **kwargs):
        """
        发送PUT请求
        :param url: 请求URL
        :param data: 请求数据
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        return self.request("PUT", url, data=data, **kwargs)
    
    def delete(self, url, **kwargs):
        """
        发送DELETE请求
        :param url: 请求URL
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        return self.request("DELETE", url, **kwargs)
    
    def upload_file(self, url, file_path, file_field="file", **kwargs):
        """
        上传文件
        :param url: 请求URL
        :param file_path: 文件路径
        :param file_field: 文件字段名
        :param kwargs: 其他关键字参数
        :return: 响应对象
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {file_field: (os.path.basename(file_path), f)}
            return self.post(url, files=files, **kwargs)
    
    def download_file(self, url, target_path, **kwargs):
        """
        下载文件
        :param url: 请求URL
        :param target_path: 保存路径
        :param kwargs: 其他关键字参数
        :return: 保存路径
        """
        response = self.get(url, stream=True, **kwargs)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 写入文件
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return target_path 