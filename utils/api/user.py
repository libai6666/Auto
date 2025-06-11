#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户相关API接口
"""

from utils.logger import logger


class UserAPI:
    """用户相关API接口封装"""
    
    @staticmethod
    def login(client, force=False):
        """
        执行登录流程
        :param client: API客户端实例
        :param force: 是否强制重新登录
        :return: 登录是否成功
        """
        # 如果已经有access_token且不强制登录，则直接返回成功
        if client.access_token and not force:
            return True
        
        import re
        
        # 第一步：发送短信验证码
        send_sms_response = client.request(
            method="POST",
            url="/api/user/v1/user/login/sendSms",
            json={
                "phoneNum": client.user_config["phoneNumber"],
                "phoneCode": client.user_config["phoneCode"]
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
        
        logger.info(f"发送短信验证码成功，手机: {client.user_config['phoneCode']}-{client.user_config['phoneNumber']}")
        
        # 获取实际验证码
        get_code_response = client.request(
            method="POST",
            url="/api/user/v1/operate/submit",
            json={
                "operateName": "admin",
                "phone": client.user_config["phoneNumber"],
                "areaCode": client.user_config["phoneCode"],
                "operate": "App短信验证码"
            }
        )
        
        # 检查获取验证码是否成功
        if get_code_response.status_code != 200:
            logger.error(f"获取验证码失败: {get_code_response.text}")
            return False
        
        code_result = get_code_response.json()
        if code_result.get("errorCode") != 0 or not code_result.get("succeed"):
            logger.error(f"获取验证码失败: {code_result.get('errorMessage')}")
            return False
        
        # 从响应中提取验证码
        code_message = code_result["data"]["jsonValue"]
        sms_code_match = re.search(r'验证码为 \[(\d+)\]', code_message)
        if not sms_code_match:
            logger.error(f"无法从响应中提取验证码: {code_message}")
            return False
        
        sms_code = sms_code_match.group(1)
        logger.info(f"成功获取验证码: {sms_code}")
        
        # 第二步：执行登录
        login_response = client.request(
            method="POST",
            url="/api/user/v1/user/login",
            json={
                "bizId": 1,
                "channel": "phone",
                "token": client.user_config["phoneNumber"],
                "phoneCode": client.user_config["phoneCode"],
                "smsCode": sms_code  # 使用提取的验证码
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
        client.access_token = login_result["data"]["accessToken"]
        client.user_info = login_result["data"]["userInfo"]
        
        # 更新Authorization头
        client.session.headers.update({"Authorization": client.access_token})
        
        # 获取用户身份描述
        role_description = UserAPI.get_user_role_description(client)
        
        logger.info(f"登录成功，用户ID: {client.user_info['uid']}, 昵称: {client.user_info['nick']}, 身份: {role_description}")
        return True
    
    @staticmethod
    def modify_nick(client, new_nick):
        """
        修改用户昵称
        :param client: API客户端实例
        :param new_nick: 新昵称
        :return: (是否成功, 响应对象)
        """
        response = client.request(
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
        if client.user_info:
            client.user_info["nick"] = new_nick
        
        logger.info(f"修改昵称成功: {new_nick}")
        return True, response
    
    @staticmethod
    def modify_profile(client, gender=None, birthday=None, country=None):
        """
        完善用户资料
        :param client: API客户端实例
        :param gender: 性别 1：男 2：女
        :param birthday: 生日，格式: YYYY-MM-DD
        :param country: 国家
        :return: (是否成功, 响应对象)
        """
        # 构建请求参数
        profile_data = {}
        if gender is not None:
            profile_data["gender"] = gender
        if birthday is not None:
            profile_data["birthday"] = birthday
        if country is not None:
            profile_data["country"] = country
            
        # 如果没有任何参数，直接返回成功
        if not profile_data:
            logger.warning("没有提供任何资料更新参数")
            return True, None
            
        response = client.request(
            method="POST",
            url="/api/user/v1/user/modifyProfile",
            json=profile_data
        )
        
        if response.status_code != 200:
            logger.error(f"完善用户资料失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"完善用户资料失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if client.user_info and result.get("data") and result["data"].get("userInfo"):
            updated_info = result["data"]["userInfo"]
            # 更新性别
            if "gender" in profile_data and "gender" in updated_info:
                client.user_info["gender"] = updated_info["gender"]
            # 更新生日
            if "birthday" in profile_data and "birthday" in updated_info:
                client.user_info["birthday"] = updated_info["birthday"]
            # 更新国家
            if "country" in profile_data and "country" in updated_info:
                client.user_info["country"] = updated_info["country"]
        
        logger.info(f"完善用户资料成功: {profile_data}")
        return True, response
    
    @staticmethod
    def get_user_role_description(client):
        """
        获取用户身份描述
        根据userRoles数组判断用户身份：
        - 只有1：用户
        - 包含2：主播
        - 包含4：代理
        - 同时包含2和4：主播和代理
        :param client: API客户端实例
        :return: 用户身份描述
        """
        if not client.user_info or "userRoles" not in client.user_info:
            return "未知"
        
        roles = client.user_info["userRoles"]
        
        # 检查是否为主播和代理
        if 2 in roles and 4 in roles:
            return "主播和代理"
        # 检查是否为主播
        elif 2 in roles:
            return "主播"
        # 检查是否为代理
        elif 4 in roles:
            return "代理"
        # 默认为普通用户
        elif 1 in roles:
            return "用户"
        else:
            return "未知" 