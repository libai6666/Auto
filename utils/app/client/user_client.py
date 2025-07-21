#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import re
import os
from utils.api_client import APIClient
from utils.logger import logger
from utils.data_handler import load_config
from utils.app.api.user import UserAPI
from utils.app.heartbeat import start_heartbeat, stop_heartbeat


class UserClient(APIClient):
    """
    代表特定用户的API客户端
    """
    def __init__(self, user_config, base_url=None, timeout=None, auto_heartbeat=False):
        """
        初始化用户客户端
        :param user_config: 用户配置字典，包含phoneNumber和phoneCode
        :param base_url: API基础URL
        :param timeout: 超时时间
        :param auto_heartbeat: 是否在登录成功后自动启动心跳，默认为False
        """
        super().__init__(base_url, timeout)
        
        self.user_config = user_config
        self.access_token = None
        self.user_info = None
        self.auto_heartbeat = auto_heartbeat
        self._heartbeat_started = False
        
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
        success = UserAPI.login(self, force, login_type)
        
        # 如果登录成功且启用了自动心跳，则启动心跳
        if success and self.auto_heartbeat and not self._heartbeat_started:
            self.start_heartbeat()
        
        return success
    
    def login_direct(self, channel="phone", token=None, password=None, phoneCode=None, smsCode=None, 
                    deviceId=None, inviteCode=None, anchorId=None, deviceType="android", bizId=1):
        """
        直接使用传入的参数执行登录流程
        :param channel: 登录渠道，支持 "phone"(手机验证码)、"google"(Google登录)、"account"(账号密码)、"apple"(Apple登录)
        :param token: 登录令牌，根据渠道不同而不同：
                     - phone: 手机号
                     - google: Google令牌
                     - account: 账号名
                     - apple: Apple令牌
        :param password: 密码（账号登录和Google登录时使用）
        :param phoneCode: 手机区号（手机登录时使用）
        :param smsCode: 短信验证码（手机登录时使用）
        :param deviceId: 设备号
        :param inviteCode: 注册邀请码
        :param anchorId: 链接地址中的主播id
        :param deviceType: 登录设备类型，如ios、android
        :param bizId: 包类型，默认为1
        :return: 登录是否成功
        """
        success = UserAPI.login_direct(
            self, channel, token, password, phoneCode, smsCode,
            deviceId, inviteCode, anchorId, deviceType, bizId
        )
        
        # 如果登录成功且启用了自动心跳，则启动心跳
        if success and self.auto_heartbeat and not self._heartbeat_started:
            self.start_heartbeat()
        
        return success
    
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
    
    def start_heartbeat(self, interval=10):
        """
        启动心跳
        :param interval: 心跳间隔（秒），默认10秒
        :return: 是否成功启动
        """
        # 检查是否已登录
        if not self.access_token or not self.user_info:
            logger.warning("用户未登录，无法启动心跳")
            return False
        
        # 启动心跳线程
        start_heartbeat(self, interval)
        self._heartbeat_started = True
        logger.info(f"已启动用户 {self.get_user_id()} 的心跳")
        return True
    
    def stop_heartbeat(self):
        """
        停止心跳
        :return: 是否成功停止
        """
        result = stop_heartbeat(self)
        if result:
            self._heartbeat_started = False
            logger.info(f"已停止用户 {self.get_user_id()} 的心跳")
        return result
    
    def __del__(self):
        """
        析构函数，确保在客户端被销毁时停止心跳
        """
        try:
            if self._heartbeat_started:
                self.stop_heartbeat()
        except:
            pass 