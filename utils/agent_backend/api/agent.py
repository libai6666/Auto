#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
from utils.logger import logger


class AgentAPI:
    """
    代理后台API封装
    """
    
    @staticmethod
    def send_code(client, area_code, phone):
        """
        发送验证码
        :param client: 代理客户端
        :param area_code: 国别码
        :param phone: 手机号
        :return: (是否成功, 响应对象)
        """
        url = f"/agent/admin/code?areaCode={area_code}&phone={phone}"
        logger.info(f"发送验证码: {area_code}-{phone}")
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.get(url)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("message") == "success":
                logger.info(f"发送验证码成功: {area_code}-{phone}")
                return True, data
            else:
                logger.error(f"发送验证码失败: {data.get('message', '未知错误')}")
        else:
            logger.error(f"发送验证码请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def get_code(client, area_code, phone):
        """
        获取验证码
        :param client: 管理客户端
        :param area_code: 国别码
        :param phone: 手机号
        :return: (是否成功, 验证码, 响应对象)
        """
        url = "/api/user/v1/operate/submit"
        logger.info(f"获取验证码: {area_code}-{phone}")
        
        data = {
            "operateName": "admin",
            "phone": phone,
            "areaCode": area_code,
            "operate": "代理短信验证码"
        }
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("succeed", False):
                # 提取验证码
                json_value = data.get("data", {}).get("jsonValue", "")
                logger.info(f"原始验证码响应: {json_value}")
                
                # 直接提取所有数字，然后取最后6位作为验证码
                digits = ''.join(re.findall(r'\d', json_value))
                logger.info(f"提取的所有数字: {digits}")
                
                if len(digits) >= 6:
                    # 取最后6位数字作为验证码
                    code = digits[-6:]
                    logger.info(f"获取验证码成功(最后6位): {code}")
                    return True, code, data
                else:
                    # 如果没有足够的数字，尝试使用正则表达式
                    logger.warning(f"未找到足够的数字，尝试使用正则表达式")
                    
                    # 尝试匹配标准格式 [123456]
                    code_match = re.search(r"\[([0-9]{6})\]", json_value)
                    
                    # 如果失败，尝试匹配最后出现的6位数字
                    if not code_match:
                        # 使用非贪婪匹配和正向环视，确保匹配最后一个6位数字
                        code_match = re.search(r".*?([0-9]{6})(?![0-9])", json_value)
                    
                    if code_match:
                        code = code_match.group(1)
                        logger.info(f"通过正则表达式获取验证码成功: {code}")
                        return True, code, data
                    else:
                        logger.error(f"无法从响应中提取验证码: {json_value}")
            else:
                logger.error(f"获取验证码失败: {data.get('errorMessage', '未知错误')}")
        else:
            logger.error(f"获取验证码请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, None, response.json() if response.text else {}

    @staticmethod
    def register_agent(client, area_code, phone, code=None, invite_code=None, agent_name=None, country=None, 
                      password=None, parent_invite_code=None, login_type="1"):
        """
        注册或登录代理
        :param client: 代理客户端
        :param area_code: 国别码，必须
        :param phone: 手机号，必须
        :param code: 验证码，非必须，验证码登录(loginType=1)必传
        :param invite_code: 邀请码，必须，注册必传
        :param agent_name: 代理名称，非必须，登录方式为3(邀请链接注册)时必传
        :param country: 国家，非必须，登录方式为3(邀请链接注册)时必传
        :param password: 密码，非必须，密码登录(loginType=2)必传
        :param parent_invite_code: 父代理邀请码，非必须，登录方式为3(邀请链接注册)时必传
        :param login_type: 登录方式，必须，1：短信验证码登录，2：密码登录，3：邀请链接注册
        :return: (是否成功, 响应对象)
        """
        url = "/agent/admin/login"
        logger.info(f"注册/登录代理: {area_code}-{phone}, 登录方式: {login_type}")
        
        # 构建请求数据
        data = {
            "areaCode": area_code,
            "phone": phone,
            "loginType": login_type
        }
        
        # 根据登录方式添加必要参数
        if login_type == "1":  # 短信验证码登录
            if not code:
                logger.error("验证码登录必须提供验证码")
                return False, {"message": "验证码不能为空"}
            data["code"] = code
            data["inviteCode"] = invite_code
        elif login_type == "2":  # 密码登录
            if not password:
                logger.error("密码登录必须提供密码")
                return False, {"message": "密码不能为空"}
            data["password"] = password
        elif login_type == "3":  # 邀请链接注册
            if not code:
                logger.error("注册必须提供验证码")
                return False, {"message": "验证码不能为空"}
            if not invite_code:
                logger.error("注册必须提供邀请码")
                return False, {"message": "邀请码不能为空"}
            if not agent_name:
                logger.error("注册必须提供代理名称")
                return False, {"message": "代理名称不能为空"}
            if not country:
                logger.error("注册必须提供国家")
                return False, {"message": "国家不能为空"}
            
            data["code"] = code
            data["inviteCode"] = invite_code
            data["agentName"] = agent_name
            data["country"] = country
            
            # 如果提供了父代理邀请码，则添加
            if parent_invite_code:
                data["parentInviteCode"] = parent_invite_code
        
        # 记录请求参数
        log_data = data.copy()
        if "password" in log_data:
            log_data["password"] = "******"  # 日志中隐藏密码
        logger.debug(f"请求参数: {log_data}")
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("message") == "success":
                # 设置代理客户端的信息
                client.set_token(data.get("token"))
                client.set_agent_info(
                    data.get("agentId"),
                    agent_name or phone,  # 如果没有提供代理名称，则使用手机号
                    phone,
                    area_code
                )
                logger.info(f"注册/登录代理成功: ID={data.get('agentId')}, 手机号={area_code}-{phone}")
                return True, data
            else:
                logger.error(f"注册/登录代理失败: {data.get('message', '未知错误')}")
        else:
            logger.error(f"注册/登录代理请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def set_password(client):
        """
        设置密码接口
        :param client: 代理客户端
        :return: (是否成功, 响应对象)
        """
        url = "/agent/admin/set/password"
        logger.info("调用设置密码接口")
        
        # 检查客户端是否已登录
        if not client.is_logged_in():
            logger.error("客户端未登录，无法调用设置密码接口")
            return False, {"message": "客户端未登录"}
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.get(url)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("message") == "success":
                # 提取响应数据
                response_data = data.get("data", {})
                agent_id = response_data.get("agentId")
                is_upload = response_data.get("isUpload")
                checked = response_data.get("checked")
                username = response_data.get("username")
                password_set = response_data.get("passwordSet")
                coin_merchant = response_data.get("coinMerchant")
                
                logger.info(f"设置密码接口调用成功: 代理ID={agent_id}, 用户名={username}")
                logger.info(f"是否上传国家和名称: {is_upload}, 是否通过审核: {checked}, 是否设置密码: {password_set}, 是否商户: {coin_merchant}")
                
                return True, data
            else:
                logger.error(f"设置密码接口调用失败: {data.get('message', '未知错误')}")
        else:
            logger.error(f"设置密码接口请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {} 