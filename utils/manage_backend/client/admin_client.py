#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.api_client import APIClient
from utils.logger import logger


class AdminClient(APIClient):
    """
    管理后台API客户端，处理管理后台的请求
    """
    def __init__(self, base_url=None, timeout=None):
        """
        初始化管理后台客户端
        :param base_url: API基础URL
        :param timeout: 超时时间
        """
        super().__init__(base_url, timeout)
        
        # 设置管理后台特定的请求头
        self.admin_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        
        # 更新会话头
        self.session.headers.update(self.admin_headers)
        
        # 管理员信息
        self.token = None
        self.username = None
        self.is_admin = False
    
    def set_token(self, token):
        """
        设置管理员Token
        :param token: 管理员Token
        """
        self.token = token
        # 使用 Bearer 前缀，确保格式正确
        token_value = f"Bearer {token}" if not token.startswith("Bearer ") else token
        self.session.headers.update({"Authorization": token_value})
        logger.info("已设置管理员Token")
    
    def clear_token(self):
        """清除Token"""
        self.token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        logger.info("已清除管理员Token")
    
    def is_logged_in(self):
        """
        检查管理员是否已登录
        :return: 是否已登录
        """
        return self.token is not None
    
    def set_admin_info(self, username, is_admin=False):
        """
        设置管理员信息
        :param username: 用户名
        :param is_admin: 是否为管理员
        """
        self.username = username
        self.is_admin = is_admin
        logger.info(f"已设置管理员信息: 用户名={username}, 是否管理员={is_admin}")
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, **kwargs):
        """
        重写请求方法，确保设置正确的Host和Authorization
        :param method: 请求方法
        :param url: 请求URL
        :param params: URL参数
        :param data: 请求数据
        :param json: JSON数据
        :param headers: 请求头
        :param files: 文件
        :param kwargs: 其他参数
        :return: 响应对象
        """
        # 合并自定义头部
        merged_headers = {}
        merged_headers.update(self.admin_headers)
        
        # 确保Authorization头被包含（如果已设置）
        if self.token:
            token_value = f"Bearer {self.token}" if not self.token.startswith("Bearer ") else self.token
            merged_headers["Authorization"] = token_value
            logger.info(f"请求中包含Authorization头: {token_value[:15]}...")
        
        # 合并自定义头部
        if headers:
            merged_headers.update(headers)
        
        # 从URL提取Host并设置
        if not url.startswith(('http://', 'https://')):
            complete_url = f"{self.base_url}{url}"
        else:
            complete_url = url
        
        # 提取域名作为Host
        import re
        host_match = re.search(r'https?://([^/]+)', complete_url)
        if host_match:
            merged_headers["Host"] = host_match.group(1)
        
        # 记录请求头信息
        logger.info(f"发送请求到 {url} 的头信息:")
        for key, value in merged_headers.items():
            if key.lower() in ["authorization", "token"]:
                logger.info(f"  {key}: {value[:15]}...")
            else:
                logger.info(f"  {key}: {value}")
        
        # 发送请求
        return super().request(method, url, params, data, json, merged_headers, files, **kwargs) 