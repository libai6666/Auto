#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import json
from utils.data_handler import load_test_data, replace_variables
from utils.assert_utils import assert_response


@allure.feature("邮箱服务")
class TestEmailAPI:
    """邮箱服务API测试"""
    
    @allure.story("发送邮箱验证码")
    @allure.title("测试邮箱绑定发送验证码")
    @pytest.mark.smoke
    def test_email_send_code_bind(self, api_client):
        """测试邮箱绑定发送验证码"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_email_send_code_bind")
        
        # 替换变量
        test_data = replace_variables(test_data)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            data=test_data["request"]["data"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
        
        # 记录请求和响应
        allure.attach(
            f"请求数据: {test_data['request']['data']}",
            name="请求数据",
            attachment_type=allure.attachment_type.TEXT
        )
        
        try:
            allure.attach(
                json.dumps(response.json(), ensure_ascii=False, indent=2),
                name="响应数据",
                attachment_type=allure.attachment_type.JSON
            )
        except:
            allure.attach(
                response.text,
                name="响应数据",
                attachment_type=allure.attachment_type.TEXT
            )
    
    @allure.story("发送邮箱验证码")
    @allure.title("测试邮箱重置密码发送验证码")
    @pytest.mark.smoke
    def test_email_send_code_reset_password(self, api_client):
        """测试邮箱重置密码发送验证码"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_email_send_code_reset_password")
        
        # 替换变量
        test_data = replace_variables(test_data)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            data=test_data["request"]["data"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
    
    @allure.story("发送邮箱验证码")
    @allure.title("测试邮箱解绑发送验证码")
    @pytest.mark.smoke
    def test_email_send_code_unbind(self, api_client):
        """测试邮箱解绑发送验证码"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_email_send_code_unbind")
        
        # 替换变量
        test_data = replace_variables(test_data)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            data=test_data["request"]["data"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
    
    @allure.story("发送邮箱验证码")
    @allure.title("测试邮箱发送验证码参数异常 - 无效的类型")
    @pytest.mark.negative
    def test_email_send_code_invalid_type(self, api_client):
        """测试邮箱发送验证码参数异常 - 无效的类型"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_email_send_code_invalid_type")
        
        # 替换变量
        test_data = replace_variables(test_data)
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            data=test_data["request"]["data"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])
    
    @allure.story("发送邮箱验证码")
    @allure.title("测试邮箱发送验证码参数异常 - 无效的邮箱")
    @pytest.mark.negative
    def test_email_send_code_invalid_email(self, api_client):
        """测试邮箱发送验证码参数异常 - 无效的邮箱"""
        # 加载测试数据
        test_data = load_test_data("user.yaml", "test_email_send_code_invalid_email")
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            data=test_data["request"]["data"]
        )
        
        # 断言
        assert_response(response, test_data["expected"])