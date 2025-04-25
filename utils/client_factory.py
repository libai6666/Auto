#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.user_client import UserClient
from utils.logger import logger
from utils.data_handler import load_config


class ClientFactory:
    """
    客户端工厂，用于创建和管理用户客户端
    """
    def __init__(self):
        try:
            self.user_configs = load_config("users.yaml")
            logger.info(f"已加载 {len(self.user_configs)} 个用户配置")
        except Exception as e:
            logger.warning(f"加载用户配置失败: {str(e)}，将使用空配置")
            self.user_configs = {}
        
        self.clients = {}  # 缓存已创建的客户端
    
    def get_client(self, user_id):
        """
        获取指定用户的客户端
        :param user_id: 用户配置ID
        :return: UserClient实例
        """
        # 检查缓存中是否已有此客户端
        if user_id in self.clients:
            return self.clients[user_id]
        
        # 检查用户配置是否存在
        if user_id not in self.user_configs:
            logger.error(f"未找到用户配置: {user_id}")
            return None
        
        # 创建新客户端
        client = UserClient(self.user_configs[user_id])
        self.clients[user_id] = client
        
        return client
    
    def create_custom_client(self, phone_number, phone_code, description=None):
        """
        创建自定义用户客户端
        :param phone_number: 手机号
        :param phone_code: 国家代码
        :param description: 描述
        :return: UserClient实例
        """
        user_config = {
            "phoneNumber": phone_number,
            "phoneCode": phone_code,
            "description": description or f"自定义用户 {phone_code}-{phone_number}"
        }
        
        # 生成唯一ID
        user_id = f"custom_{phone_code}_{phone_number}"
        
        # 创建客户端
        client = UserClient(user_config)
        self.clients[user_id] = client
        
        return client
    
    def create_clients(self, count, base_phone="9000000000", phone_code="1"):
        """
        批量创建多个用户客户端
        :param count: 要创建的客户端数量
        :param base_phone: 基础电话号码，会递增
        :param phone_code: 国家代码
        :return: 客户端列表
        """
        clients = []
        base_num = int(base_phone)
        
        for i in range(count):
            phone = str(base_num + i)
            client = self.create_custom_client(phone, phone_code, f"批量用户{i+1}")
            clients.append(client)
        
        return clients

    def get_all_clients(self):
        """获取所有已创建的客户端"""
        return self.clients 