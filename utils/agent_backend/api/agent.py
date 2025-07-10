#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
from utils.logger import logger


class AgentAPI:
    """
    代理后台公共分类模块API封装
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
        logger.debug(f"请求参数: {log_data}")
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                # 从嵌套的data字段中获取token和agentId
                agent_data = response_data.get("data", {})
                token = agent_data.get("token")
                agent_id = agent_data.get("agentId")
                
                # 设置代理客户端的信息
                client.set_token(token)
                client.set_agent_info(
                    agent_id,
                    agent_name or f"{area_code}{phone}",  # 如果没有提供代理名称，则使用完整手机号
                    phone,
                    area_code
                )
                logger.info(f"注册/登录代理成功: ID={agent_id}, 手机号={area_code}-{phone}")
                return True, agent_data
            else:
                logger.error(f"注册/登录代理失败: {response_data.get('message', '未知错误')}")
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
    def set_password(client, password, confirm_password=None):
        """
        设置密码接口
        :param client: 代理客户端
        :param password: 密码，必须
        :param confirm_password: 确认密码，如果不提供则与密码相同
        :return: (是否成功, 响应对象)
        """
        url = "/agent/admin/set/password"
        logger.info("设置代理密码")
        
        # 检查客户端是否已登录
        if not client.is_logged_in():
            logger.error(f"客户端未登录，无法调用设置密码接口。Token状态: {client.token is not None}, Agent ID: {client.agent_id}")
            return False, {"message": "客户端未登录"}
        
        # 如果未提供确认密码，则使用密码
        if confirm_password is None:
            confirm_password = password
        
        # 构建请求数据
        data = {
            "password": password,
            "confirmPassword": confirm_password
        }
        
        # 记录请求参数（不记录实际密码值）
        logger.debug(f"请求参数: 密码长度={len(password)}, 确认密码长度={len(confirm_password)}")
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                logger.info(f"设置密码成功: 代理ID={client.agent_id}")
                return True, response_data
            else:
                logger.error(f"设置密码失败: {response_data.get('message', '未知错误')}")
        else:
            logger.error(f"设置密码请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}
        
    @staticmethod
    def fill_agent_info(client, agent_id, agent_name, country):
        """
        设置代理信息
        :param client: 代理客户端
        :param agent_id: 代理ID，必须
        :param agent_name: 代理名称，必须
        :param country: 国家，必须
        :return: (是否成功, 响应对象)
        """
        url = "/agent/admin/fill/info"
        logger.info(f"设置代理信息: ID={agent_id}, 名称={agent_name}, 国家={country}")
        
        # 检查客户端是否已登录
        if not client.is_logged_in():
            logger.error(f"客户端未登录，无法调用设置代理信息接口。Token状态: {client.token is not None}, Agent ID: {client.agent_id}")
            return False, {"message": "客户端未登录"}
        
        # 构建请求数据
        data = {
            "agentId": agent_id,
            "agentName": agent_name,
            "country": country
        }
        
        # 记录请求参数
        logger.debug(f"请求参数: {data}")
        
        # 客户端会自动添加请求头，包括agentId等信息
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                logger.info(f"设置代理信息成功: ID={agent_id}, 名称={agent_name}, 国家={country}")
                return True, response_data
            else:
                logger.error(f"设置代理信息失败: {response_data.get('message', '未知错误')}")
        else:
            logger.error(f"设置代理信息请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {} 

    @staticmethod
    def login(client, area_code, phone, password=None, code=None, login_type="1"):
        """
        代理登录
        :param client: 代理客户端
        :param area_code: 国别码
        :param phone: 手机号
        :param password: 密码，登录方式为2时必传
        :param code: 验证码，登录方式为1时必传
        :param login_type: 登录方式，1：短信验证码登录，2：密码登录
        :return: (是否成功, 响应对象)
        """
        logger.info(f"代理登录: {area_code}-{phone}, 登录方式: {login_type}")
        
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
        elif login_type == "2":  # 密码登录
            if not password:
                logger.error("密码登录必须提供密码")
                return False, {"message": "密码不能为空"}
            data["password"] = password
        
        # 记录请求参数（不记录密码）
        log_data = data.copy()
        if "password" in log_data:
            log_data["password"] = "******"
        logger.debug(f"请求参数: {log_data}")
        
        # 发送请求
        url = "/agent/admin/login"
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                # 从嵌套的data字段中获取token和agentId
                agent_data = response_data.get("data", {})
                token = agent_data.get("token")
                agent_id = agent_data.get("agentId")
                
                # 设置代理客户端的信息
                client.set_token(token)
                client.set_agent_info(
                    agent_id,
                    agent_data.get("username", f"{area_code}{phone}"),
                    phone,
                    area_code
                )
                logger.info(f"代理登录成功: ID={agent_id}, 手机号={area_code}-{phone}")
                return True, agent_data
            else:
                logger.error(f"代理登录失败: {response_data.get('message', '未知错误')}")
        else:
            logger.error(f"代理登录请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}
    
    @staticmethod
    def get_bind_list(client, page_index=1, page_size=10, agent_id=None, actor_id=None):
        """
        获取主播绑定申请列表
        :param client: 代理客户端
        :param page_index: 页码，从1开始
        :param page_size: 每页数量
        :param agent_id: 代理ID，可选
        :param actor_id: 主播ID，可选
        :return: (是否成功, 绑定列表, 响应对象)
        """
        logger.info(f"获取主播绑定申请列表: 页码={page_index}, 每页数量={page_size}")
        
        # 检查客户端是否已登录
        if not client.is_logged_in():
            logger.error("客户端未登录，无法获取主播绑定申请列表")
            return False, None, {"message": "客户端未登录"}
        
        # 构建请求参数
        params = {
            "pageIndex": page_index,
            "pageSize": page_size
        }
        
        # 如果提供了代理ID，则添加
        if agent_id:
            params["agentId"] = agent_id
        elif client.agent_id:
            # 如果没有提供代理ID，但客户端有代理ID，则使用客户端的代理ID
            params["agentId"] = client.agent_id
        else:
            logger.error("未提供代理ID，且客户端无代理ID信息")
            return False, None, {"message": "未提供代理ID"}
        
        # 如果提供了主播ID，则添加
        if actor_id:
            params["actorId"] = actor_id
        
        # 发送请求
        url = "/agent/admin/actor/bind/list"
        response = client.get(url, params=params)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                bind_data = response_data.get("data", {})
                records = bind_data.get("records", [])
                total = bind_data.get("total", 0)
                logger.info(f"获取主播绑定申请列表成功: 总数={total}, 当前页记录数={len(records)}")
                return True, records, response_data
            else:
                logger.error(f"获取主播绑定申请列表失败: {response_data.get('message', '未知错误')}")
        else:
            logger.error(f"获取主播绑定申请列表请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, None, response.json() if response.text else {}
    
    @staticmethod
    def check_bind(client, record_id, status):
        """
        审核主播绑定申请
        :param client: 代理客户端
        :param record_id: 记录ID
        :param status: 状态：3:已通过 4：已拒绝
        :return: (是否成功, 响应对象)
        """
        logger.info(f"审核主播绑定申请: 记录ID={record_id}, 状态={status}")
        
        # 检查客户端是否已登录
        if not client.is_logged_in():
            logger.error("客户端未登录，无法审核主播绑定申请")
            return False, {"message": "客户端未登录"}
        
        # 检查状态是否合法
        if status not in [3, 4]:
            logger.error(f"状态值不合法: {status}，必须是3(通过)或4(拒绝)")
            return False, {"message": "状态值不合法"}
        
        # 构建请求数据
        data = {
            "id": record_id,
            "status": status
        }
        
        # 发送请求
        url = "/agent/admin/actor/bind/check"
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0 and response_data.get("message") == "success":
                status_text = "通过" if status == 3 else "拒绝"
                logger.info(f"审核主播绑定申请{status_text}成功: 记录ID={record_id}")
                return True, response_data
            else:
                logger.error(f"审核主播绑定申请失败: {response_data.get('message', '未知错误')}")
        else:
            logger.error(f"审核主播绑定申请请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {} 