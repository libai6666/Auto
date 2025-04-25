#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import time
import threading
import random
import string
from utils.logger import logger

# 生成随机字母字符串的辅助函数
def random_string(length=8):
    """生成随机字母字符串"""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

@allure.feature("用户功能")
class TestUserNick:
    """用户昵称修改测试"""
    
    @allure.story("昵称修改")
    @allure.title("测试单个用户修改昵称成功-纯英文")
    @pytest.mark.smoke
    def test_modify_nick_success(self, client_factory):
        """测试单个用户修改昵称成功-纯英文"""
        # 获取测试客户端
        client = client_factory.get_client("user1")
        
        # 确保登录
        assert client.login(), "用户登录失败"
        
        # 生成一个纯英文昵称
        new_nick = f"User{random_string(5)}"
        
        # 修改昵称
        success, response = client.modify_nick(new_nick)
        
        # 断言
        assert success, f"修改昵称失败: {response.text if response else '无响应'}"
        
        # 检查响应
        result = response.json()
        assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
        
        # 记录请求和响应
        allure.attach(
            f"修改昵称为: {new_nick}",
            name="请求数据",
            attachment_type=allure.attachment_type.TEXT
        )
        allure.attach(
            f"{response.text}",
            name="响应数据",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.story("昵称修改")
    @allure.title("测试单个用户修改昵称失败-纯数字")
    @pytest.mark.negative
    def test_modify_nick_failure_numbers(self, client_factory):
        """测试单个用户修改昵称失败-纯数字"""
        # 获取测试客户端
        client = client_factory.get_client("user2")
        
        # 确保登录
        assert client.login(), "用户登录失败"
        
        # 生成一个纯数字昵称
        timestamp = int(time.time())
        new_nick = f"{timestamp}"
        
        # 修改昵称
        success, response = client.modify_nick(new_nick)
        
        # 断言应该失败
        assert not success, "纯数字昵称应该修改失败，但实际成功了"
        
        # 检查响应
        result = response.json()
        assert result["errorCode"] != 0, "使用纯数字昵称时错误码应该不为0"
        
        # 记录请求和响应
        allure.attach(
            f"修改昵称为: {new_nick}",
            name="请求数据",
            attachment_type=allure.attachment_type.TEXT
        )
        allure.attach(
            f"{response.text}",
            name="响应数据",
            attachment_type=allure.attachment_type.TEXT
        )
    
    @allure.story("昵称修改")
    @pytest.mark.skip(reason="并发修改昵称测试，跳过")
    @allure.title("测试多个用户同时修改昵称成功-纯英文")
    @pytest.mark.smoke
    def test_multi_users_modify_nick(self, client_factory):
        """测试多个用户同时修改昵称成功-纯英文"""
        # 获取多个客户端
        client1 = client_factory.get_client("user1")
        client2 = client_factory.get_client("user2")
        client3 = client_factory.get_client("user3")
        
        # 确保所有客户端都已登录
        for i, client in enumerate([client1, client2, client3], 1):
            assert client.login(), f"用户{i}登录失败"
        
        # 生成唯一的英文昵称
        new_nick1 = f"zbUser{random_string(4)}"
        new_nick2 = f"zbUser{random_string(4)}"
        new_nick3 = f"User{random_string(4)}"
        
        # 结果列表
        results = [None, None, None]
        
        # 定义修改昵称的函数
        def modify_nick(client, new_nick, index):
            success, response = client.modify_nick(new_nick)
            results[index] = (success, response)
        
        # 创建线程
        threads = [
            threading.Thread(target=modify_nick, args=(client1, new_nick1, 0)),
            threading.Thread(target=modify_nick, args=(client2, new_nick2, 1)),
            threading.Thread(target=modify_nick, args=(client3, new_nick3, 2))
        ]
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        all_success = True
        for i, (success, response) in enumerate(results, 1):
            if not success:
                all_success = False
                logger.error(f"用户{i}修改昵称失败: {response.text if response else '无响应'}")
            else:
                result = response.json()
                if result["errorCode"] != 0:
                    all_success = False
                    logger.error(f"用户{i}响应错误码不为0: {result['errorMessage']}")
        
        # 断言
        assert all_success, "并发修改昵称测试失败，有一个或多个用户修改失败"
        
        # 记录测试信息
        allure.attach(
            f"用户1昵称: {new_nick1}\n用户2昵称: {new_nick2}\n用户3昵称: {new_nick3}",
            name="测试数据",
            attachment_type=allure.attachment_type.TEXT
        ) 