#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import re
import os
from utils.api_client import APIClient
from utils.logger import logger
from utils.data_handler import load_config
from utils.app.api.user import UserAPI


class UserClient(APIClient):
    """
    代表特定用户的API客户端
    """
    def __init__(self, user_config, base_url=None, timeout=None):
        """
        初始化用户客户端
        :param user_config: 用户配置字典，包含phoneNumber和phoneCode
        :param base_url: API基础URL
        :param timeout: 超时时间
        """
        super().__init__(base_url, timeout)
        
        self.user_config = user_config
        self.access_token = None
        self.user_info = None
        
        # 设置公共头
        common_headers = {
            "d": "111",
            "p": "1",
            "v": "5.8.1",
            "l": "zh-en",
            "appName": "duoo",
            "bizId": "1",
            "Content-Type": "application/json"
        }
        self.session.headers.update(common_headers)
    
    def login(self, force=False, login_type="phone"):
        """
        执行登录流程
        :param force: 是否强制重新登录
        :param login_type: 登录类型，支持 "phone"(手机验证码)、"google"(Google登录)、"account"(账号密码)
        :return: 登录是否成功
        """
        return UserAPI.login(self, force, login_type)
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, auto_login=True, **kwargs):
        """
        重写请求方法，添加自动登录功能
        :param method: 请求方法
        :param url: 请求URL
        :param params: URL参数
        :param data: 请求数据
        :param json: JSON数据
        :param headers: 请求头
        :param files: 文件
        :param auto_login: 是否自动登录，默认为True
        :param kwargs: 其他参数
        :return: 响应对象
        """
        # 自动登录（如果需要且不是登录相关接口）
        if auto_login and not self.access_token and not url.endswith(("login/sendSms", "login", "operate/submit")):
            logger.info("需要登录后才能访问，正在自动登录...")
            if not self.login():
                raise Exception("自动登录失败，无法继续请求")
        
        # 发送请求
        return super().request(method, url, params, data, json, headers, files, **kwargs)
    
    def get_user_id(self):
        """获取用户ID"""
        return self.user_info["uid"] if self.user_info else None
    
    def get_user_nick(self):
        """获取用户昵称"""
        return self.user_info["nick"] if self.user_info else None
    
    def get_user_role(self):
        """获取用户角色"""
        return self.user_info["userRoles"][0] if self.user_info and "userRoles" in self.user_info else None 