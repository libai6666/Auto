#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from utils.api_client import APIClient
from utils.logger import logger


class GuestClient(APIClient):
    """
    访客用户客户端，用于访客登录
    """
    BIZ_ID = "6"

    def __init__(self, base_url=None, timeout=None):
        super().__init__(base_url, timeout)
        self.access_token = None
        self.user_info = None

        # 设置公共头
        common_headers = {
            # 每个访客使用独立随机设备号，prod对单设备访客登录数有限制(errorCode 101005 Your device is limited)
            "d": uuid.uuid4().hex,
            "p": "1",
            "v": "5.8.1",
            "l": "zh-en",
            "appName": "duoo",
            "bizId": self.BIZ_ID,
            "Content-Type": "application/json"
        }
        self.session.headers.update(common_headers)

    def guest_login(self):
        """
        访客登录
        :return: 登录是否成功
        """
        # 生成随机UUID作为token
        guest_token = str(uuid.uuid4())

        login_data = {
            "bizId": 6,
            "channel": "guest",
            "token": guest_token,
            "phoneCode": None,
            "smsCode": None,
            "password": None,
            "installReferrer": None,
            "inviteCode": None,
            "limitedUseAppCheckToken": None,
            "anchorId": 0,
            "shareId": 0
        }

        try:
            response = self.request(
                method="POST",
                url="/api/user/v1/user/login",
                json=login_data
            )

            if response.status_code != 200:
                logger.error(f"访客登录失败: {response.text}")
                return False

            result = response.json()
            if result.get("errorCode") != 0:
                logger.error(f"访客登录失败: {result.get('errorMessage')}")
                return False

            # 保存token和用户信息
            self.access_token = result["data"]["accessToken"]
            self.user_info = result["data"]["userInfo"]

            # 更新Authorization头
            self.session.headers.update({"Authorization": self.access_token})

            logger.info(f"访客登录成功，用户ID: {self.user_info['uid']}, 昵称: {self.user_info.get('nick', 'Guest')}")
            return True

        except Exception as e:
            logger.error(f"访客登录异常: {str(e)}")
            return False

    def get_user_id(self):
        """获取用户ID"""
        return self.user_info["uid"] if self.user_info else None
