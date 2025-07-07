#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.api_client import APIClient
from utils.logger import logger


class AgentClient(APIClient):
    """
    代理后台API客户端，处理代理后台的请求
    """
    def __init__(self, base_url=None, timeout=None):
        """
        初始化代理后台客户端
        :param base_url: API基础URL
        :param timeout: 超时时间
        """
        super().__init__(base_url, timeout)
        
        # 设置代理后台特定的请求头
        self.agent_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        # 更新会话头
        self.session.headers.update(self.agent_headers)
        
        # 代理信息
        self.token = None
        self.agent_id = None
        self.agent_name = None
        self.phone = None
        self.area_code = None
    
    def set_token(self, token):
        """
        设置代理Token
        :param token: 代理Token
        """
        self.token = token
        self.session.headers.update({"Token": token})
        logger.info("已设置代理Token")
    
    def clear_token(self):
        """清除Token"""
        self.token = None
        if "Token" in self.session.headers:
            del self.session.headers["Token"]
        logger.info("已清除代理Token")
    
    def is_logged_in(self):
        """
        检查代理是否已登录
        :return: 是否已登录
        """
        return self.token is not None
    
    def set_agent_info(self, agent_id, agent_name, phone, area_code):
        """
        设置代理信息
        :param agent_id: 代理ID
        :param agent_name: 代理名称
        :param phone: 手机号
        :param area_code: 国别码
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.phone = phone
        self.area_code = area_code
        logger.info(f"已设置代理信息: ID={agent_id}, 名称={agent_name}")
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, **kwargs):
        """
        重写请求方法，确保设置正确的Host
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
        merged_headers.update(self.agent_headers)
        
        # 如果设置了代理ID，则添加到请求头中
        if self.agent_id:
            merged_headers["agentId"] = str(self.agent_id)
            
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
        
        # 发送请求
        return super().request(method, url, params, data, json, merged_headers, files, **kwargs) 