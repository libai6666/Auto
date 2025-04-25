#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from utils.api_client import APIClient
from utils.logger import logger
from utils.data_handler import load_config


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
    
    def login(self, force=False):
        """
        执行登录流程
        :param force: 是否强制重新登录
        :return: 登录是否成功
        """
        if self.access_token and not force:
            return True
        
        # 第一步：发送短信验证码
        send_sms_response = super().request(
            method="POST",
            url="/api/user/v1/user/login/sendSms",
            json={
                "phoneNum": self.user_config["phoneNumber"],
                "phoneCode": self.user_config["phoneCode"]
            }
        )
        
        # 检查发送短信是否成功
        if send_sms_response.status_code != 200:
            logger.error(f"发送短信验证码失败: {send_sms_response.text}")
            return False
        
        sms_result = send_sms_response.json()
        if sms_result.get("errorCode") != 0:
            logger.error(f"发送短信验证码失败: {sms_result.get('errorMessage')}")
            return False
        
        logger.info(f"发送短信验证码成功，手机: {self.user_config['phoneCode']}-{self.user_config['phoneNumber']}")
        
        # 第二步：执行登录
        login_response = super().request(
            method="POST",
            url="/api/user/v1/user/login",
            json={
                "bizId": 1,
                "channel": "phone",
                "token": self.user_config["phoneNumber"],
                "phoneCode": self.user_config["phoneCode"],
                "smsCode": "123456"  # 固定验证码
            }
        )
        
        # 检查登录是否成功
        if login_response.status_code != 200:
            logger.error(f"登录失败: {login_response.text}")
            return False
        
        login_result = login_response.json()
        if login_result.get("errorCode") != 0:
            logger.error(f"登录失败: {login_result.get('errorMessage')}")
            return False
        
        # 保存token和用户信息
        self.access_token = login_result["data"]["accessToken"]
        self.user_info = login_result["data"]["userInfo"]
        
        # 更新Authorization头
        self.session.headers.update({"Authorization": self.access_token})
        
        logger.info(f"登录成功，用户ID: {self.user_info['uid']}, 昵称: {self.user_info['nick']}")
        return True
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, **kwargs):
        """
        重写请求方法，添加自动登录功能
        """
        # 自动登录（如果需要且不是登录相关接口）
        if not self.access_token and not url.endswith(("login/sendSms", "login")):
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
    
    def modify_nick(self, new_nick):
        """
        修改用户昵称
        :param new_nick: 新昵称
        :return: 是否成功
        """
        response = self.request(
            method="POST",
            url="/api/user/v1/user/modifyNick",
            json={"nick": new_nick}
        )
        
        if response.status_code != 200:
            logger.error(f"修改昵称失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"修改昵称失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if self.user_info:
            self.user_info["nick"] = new_nick
        
        logger.info(f"修改昵称成功: {new_nick}")
        return True, response 