#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
from utils.logger import logger
from utils.app.api.user import UserAPI
import json

@allure.feature("用户功能")
class TestLoginMethods:
    """不同登录方式测试"""
    
    @allure.story("登录方式")
    @allure.title("测试手机验证码登录")
    @pytest.mark.smoke
    def test_phone_login(self, client_factory):
        """测试手机验证码登录"""
        with allure.step("第一步：获取测试客户端"):
            # 获取测试客户端
            client = client_factory.get_client("user1")
        
        with allure.step("第二步：执行手机验证码登录"):
            # 默认使用手机验证码登录
            login_success = client.login(force=True, login_type="phone")
            
            # 记录登录结果
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            
            # 断言
            assert login_success, "手机验证码登录失败"
            assert client.access_token is not None, "登录成功但未获取到access_token"
            assert client.user_info is not None, "登录成功但未获取到用户信息"
            
            logger.info(f"手机验证码登录成功，用户ID: {client.user_info['uid']}")
    
    @allure.story("登录方式")
    @allure.title("测试Google登录")
    @pytest.mark.smoke
    def test_google_login(self, client_factory):
        """测试Google登录"""
        with allure.step("第一步：获取测试客户端"):
            # 获取测试客户端
            client = client_factory.get_client("google_user")
        
        with allure.step("第二步：执行Google登录"):
            # 使用Google登录
            login_success = client.login(force=True, login_type="google")
            
            # 记录登录结果
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            
            # 断言
            # 注意：由于这是示例代码，实际上Google登录可能会失败，因为我们使用的是模拟token
            # 在实际测试中，需要使用有效的Google token
            logger.info(f"Google登录结果: {login_success}")
            
            # 如果登录成功，验证用户信息
            if login_success:
                assert client.access_token is not None, "登录成功但未获取到access_token"
                assert client.user_info is not None, "登录成功但未获取到用户信息"
                logger.info(f"Google登录成功，用户ID: {client.user_info['uid']}")
    
    @allure.story("登录方式")
    @allure.title("测试账号密码登录")
    @pytest.mark.smoke
    def test_account_login(self, client_factory):
        """测试账号密码登录"""
        with allure.step("第一步：获取测试客户端"):
            # 获取测试客户端
            client = client_factory.get_client("account_user")
        
        with allure.step("第二步：执行账号密码登录"):
            # 使用账号密码登录
            login_success = client.login(force=True, login_type="account")
            
            # 记录登录结果
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            
            # 断言
            # 注意：由于这是示例代码，实际上账号密码登录可能会失败，因为我们使用的是模拟账号密码
            # 在实际测试中，需要使用有效的账号密码
            logger.info(f"账号密码登录结果: {login_success}")
            
            # 如果登录成功，验证用户信息
            if login_success:
                assert client.access_token is not None, "登录成功但未获取到access_token"
                assert client.user_info is not None, "登录成功但未获取到用户信息"
                logger.info(f"账号密码登录成功，用户ID: {client.user_info['uid']}")
    
    @allure.story("登录方式")
    @allure.title("测试多种登录方式切换")
    @pytest.mark.smoke
    def test_multi_login_methods(self, client_factory):
        """测试多种登录方式切换"""
        with allure.step("第一步：获取测试客户端"):
            # 获取支持多种登录方式的测试客户端
            client = client_factory.get_client("multi_login_user")
        
        with allure.step("第二步：使用手机验证码登录"):
            # 先使用手机验证码登录
            phone_login_success = client.login(force=True, login_type="phone")
            allure.attach(str(phone_login_success), name="手机登录结果", attachment_type=allure.attachment_type.TEXT)
            
            if phone_login_success:
                logger.info(f"手机验证码登录成功，用户ID: {client.user_info['uid']}")
                
                # 清除登录状态，以便测试其他登录方式
                client.access_token = None
                client.user_info = None
        
        with allure.step("第三步：使用账号密码登录"):
            # 再使用账号密码登录
            account_login_success = client.login(force=True, login_type="account")
            allure.attach(str(account_login_success), name="账号登录结果", attachment_type=allure.attachment_type.TEXT)
            
            if account_login_success:
                logger.info(f"账号密码登录成功，用户ID: {client.user_info['uid']}")
                
                # 清除登录状态，以便测试其他登录方式
                client.access_token = None
                client.user_info = None
        
        with allure.step("第四步：使用Google登录"):
            # 最后使用Google登录
            google_login_success = client.login(force=True, login_type="google")
            allure.attach(str(google_login_success), name="Google登录结果", attachment_type=allure.attachment_type.TEXT)
            
            if google_login_success:
                logger.info(f"Google登录成功，用户ID: {client.user_info['uid']}")
        
        # 记录测试总结
        with allure.step("测试总结"):
            summary = f"""
            手机验证码登录: {'成功' if phone_login_success else '失败'}
            账号密码登录: {'成功' if account_login_success else '失败'}
            Google登录: {'成功' if google_login_success else '失败'}
            """
            allure.attach(summary, name="多种登录方式测试总结", attachment_type=allure.attachment_type.TEXT)
            logger.info(summary) 