#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import json
from utils.data_handler import load_test_data, replace_variables
from utils.assert_utils import assert_response


@allure.feature("用户管理")
class TestUserAPI:
    """用户管理API测试"""
    
    @allure.story("用户登录")
    @allure.title("测试成功登录")
    @pytest.mark.smoke
    def test_login_success(self, api_client):
        """测试用户成功登录"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_login_success")
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            json=test_data["request"]["json"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
    
    @allure.story("用户登录")
    @allure.title("测试错误密码登录")
    @pytest.mark.smoke
    def test_login_wrong_password(self, api_client):
        """测试错误密码登录"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_login_wrong_password")
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            json=test_data["request"]["json"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
    
    @allure.story("用户注册")
    @allure.title("测试成功注册")
    @pytest.mark.smoke
    def test_register_success(self, api_client, session_variables):
        """测试用户成功注册"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_register_success")
        
        # 替换变量
        test_data = replace_variables(test_data)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            json=test_data["request"]["json"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
        
        # 提取注册成功的用户ID
        try:
            response_json = response.json()
            user_id = response_json.get("data", {}).get("user_id")
            if user_id:
                session_variables["user_id"] = user_id
                allure.attach(
                    json.dumps({"user_id": user_id}, ensure_ascii=False),
                    name="提取的变量",
                    attachment_type=allure.attachment_type.JSON
                )
        except Exception as e:
            allure.attach(
                str(e),
                name="变量提取失败",
                attachment_type=allure.attachment_type.TEXT
            )
    
    @allure.story("用户信息")
    @allure.title("测试获取用户信息")
    @pytest.mark.smoke
    def test_get_user_info(self, api_client, session_variables):
        """测试获取用户信息"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_get_user_info")
        
        # 检查依赖变量
        if "user_id" not in session_variables or "token" not in session_variables:
            pytest.skip("缺少必要的测试数据: user_id 或 token")
        
        # 替换变量
        test_data = replace_variables(test_data, session_variables)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])