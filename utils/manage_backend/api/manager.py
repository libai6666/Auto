#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.logger import logger


class ManagerAPI:
    """
    管理后台API封装
    """
    
    @staticmethod
    def login(client, username="admin", password="W67hW7/uh9cav+hRF71uJFut0Cnrtf8T0KsaawUocDfuJAuDWr+zutnakwEybnn2WDlYAdyZiaJaNw8pH6pDzQ=="):
        """
        登录管理后台
        :param client: 管理客户端
        :param username: 用户名
        :param password: 密码
        :return: (是否成功, 响应对象)
        """
        url = "/admin/auth/login"
        logger.info(f"登录管理后台: {username}")
        
        # 构造请求数据
        data = {
            "username": username,
            "password": password
        }
        
        # 客户端会自动添加请求头
        response = client.post(url, json=data)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                # 设置管理客户端的信息
                client.set_token(data["token"])
                
                # 设置管理员信息
                user_info = data.get("user", {}).get("user", {})
                client.set_admin_info(
                    user_info.get("username"),
                    user_info.get("isAdmin", False)
                )
                
                logger.info(f"登录管理后台成功: {username}")
                return True, data
            else:
                logger.error(f"登录管理后台失败: 响应中缺少token")
        else:
            logger.error(f"登录管理后台请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def generate_invite_code(client, num=1):
        """
        生成邀请码
        :param client: 管理客户端
        :param num: 生成数量
        :return: (是否成功, 响应对象)
        """
        url = "/admin/agent/generator/invite/code"
        logger.info(f"生成邀请码: 数量={num}")
        
        # 客户端会自动添加请求头
        response = client.post(url, json={"num": num})
        
        # 检查响应
        if response.status_code in [200, 201]:  # 接受200和201状态码
            # 处理可能的空响应(201可能没有响应体)
            if not response.text:
                logger.info(f"生成邀请码成功: 状态码={response.status_code}")
                # 重新获取邀请码列表
                return ManagerAPI.get_invite_code_list(client)
            else:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"生成邀请码成功: 数量={len(data)}")
                        return True, data
                    else:
                        logger.error(f"生成邀请码失败: 响应格式不符合预期")
                except Exception as e:
                    logger.error(f"解析响应失败: {str(e)}")
        else:
            logger.error(f"生成邀请码请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def get_invite_code_list(client, page=0, size=10, sort="id,desc"):
        """
        获取邀请码列表
        :param client: 管理客户端
        :param page: 页码
        :param size: 每页数量
        :param sort: 排序方式
        :return: (是否成功, 响应对象)
        """
        url = "/admin/agent/invite/code/list"
        logger.info(f"获取邀请码列表: 页码={page}, 每页数量={size}")
        
        params = {
            "page": page,
            "size": size,
            "sort": sort
        }
        
        # 客户端会自动添加请求头
        response = client.get(url, params=params)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if "content" in data:
                logger.info(f"获取邀请码列表成功: 数量={len(data['content'])}")
                return True, data
            else:
                logger.error(f"获取邀请码列表失败: 响应格式不符合预期")
        else:
            logger.error(f"获取邀请码列表请求失败: HTTP {response.status_code}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def get_unused_invite_code(client):
        """
        获取未使用的邀请码
        :param client: 管理客户端
        :return: (是否成功, 邀请码, 响应对象)
        """
        # 获取邀请码列表
        success, data = ManagerAPI.get_invite_code_list(client)
        
        if success:
            # 查找未使用的邀请码(status=0)
            content = data.get("content", [])
            for item in content:
                if item.get("status") == 0:
                    invite_code = item.get("inviteCode")
                    logger.info(f"获取未使用的邀请码成功: {invite_code}")
                    return True, invite_code, data
            
            # 如果没有找到未使用的邀请码，则生成新的
            logger.info("未找到未使用的邀请码，正在生成新的邀请码")
            success, gen_data = ManagerAPI.generate_invite_code(client, 1)
            
            if success and gen_data:
                # 重新获取邀请码列表
                return ManagerAPI.get_unused_invite_code(client)
            else:
                logger.error("生成新邀请码失败")
                return False, None, data
        else:
            logger.error("获取邀请码列表失败")
            return False, None, data 