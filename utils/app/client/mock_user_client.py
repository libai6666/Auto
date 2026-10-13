#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.api_client import APIClient
from utils.app.api.user import UserAPI
from utils.logger import logger


class MockUserClient(APIClient):
    """
    mockRefresh登录客户端，通过uid直接获取登录态（替代手机号验证码登录）
    """
    MOCK_COUNTRY = "IN"
    MOCK_ROLE_LEVEL = 3  # 角色：1 用户、3 主播、5 代理
    BIZ_ID = "1"

    def __init__(self, base_url=None, timeout=None):
        super().__init__(base_url, timeout)
        self.access_token = None
        self.user_info = None

        # 设置公共头
        common_headers = {
            "d": "111",
            "p": "1",
            "v": "5.8.1",
            "l": "zh-en",
            "appName": "duoo",
            "bizId": self.BIZ_ID,
            "Content-Type": "application/json"
        }
        self.session.headers.update(common_headers)

    def mock_login(self, uid, country=None, role_level=None):
        """
        通过mockRefresh接口登录指定uid的用户
        :param uid: 用户ID
        :param country: 国家码，默认IN
        :param role_level: 角色等级：1 用户、3 主播、5 代理，默认3
        :return: 登录是否成功
        """
        success, access_token, user_info = UserAPI.mock_refresh(
            self, uid,
            country=country or self.MOCK_COUNTRY,
            role_level=role_level if role_level is not None else self.MOCK_ROLE_LEVEL
        )
        if not success:
            return False

        self.access_token = access_token
        self.user_info = user_info or {"uid": uid}

        # 更新Authorization头
        self.session.headers.update({"Authorization": self.access_token})

        logger.info(f"mockRefresh登录成功，用户ID: {self.user_info.get('uid', uid)}")
        return True

    def get_user_id(self):
        """获取用户ID"""
        return self.user_info["uid"] if self.user_info else None
