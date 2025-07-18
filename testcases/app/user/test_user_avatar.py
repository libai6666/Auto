#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import random
import json
from utils.logger import logger
from utils.data_handler import load_yaml_data  # 使用我们新添加的函数
from utils.app.api.user import UserAPI

@allure.feature("用户功能")
class TestUserAvatar:
    """用户头像修改测试"""
    
    @allure.story("头像修改")
    @allure.title("测试用户修改头像成功")
    @pytest.mark.smoke
    def test_modify_avatar_success(self, client_factory):
        """测试用户修改头像成功"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user1")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：加载测试数据，选择有效头像"):
            # 加载测试数据 - 正确引用data目录下的文件
            avatar_data = load_yaml_data("data/app/user.yaml")
            valid_avatars = avatar_data["avatar_test_data"]["valid_avatars"]
            
            # 随机选择一个有效的头像地址
            avatar = random.choice(valid_avatars)
            allure.attach(avatar, name="选择的头像URL", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改头像接口"):
            # 修改头像
            success, response = UserAPI.modify_avatar(client, avatar)
            
            # 断言
            assert success, f"修改头像失败: {response.text if response else '无响应'}"
        
        with allure.step("第四步：验证响应结果"):
            # 检查响应
            result = response.json()
            assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
            assert result["succeed"] == True, "响应succeed字段不为True"
            
            # 记录请求和响应
            allure.attach(
                f"修改头像为: {avatar}",
                name="请求数据",
                attachment_type=allure.attachment_type.TEXT
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
    
    @allure.story("头像修改")
    @allure.title("测试用户修改头像失败-空参数")
    @pytest.mark.medium
    def test_modify_avatar_failure_empty(self, client_factory):
        """测试用户修改头像失败-空参数"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user2")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：使用空头像地址"):
            # 使用空头像地址
            avatar = ""
            allure.attach("使用空字符串作为头像URL", name="测试数据", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改头像接口"):
            # 修改头像
            success, response = UserAPI.modify_avatar(client, avatar)
            
            # 断言应该失败
            assert not success, "空头像地址应该修改失败，但实际成功了"
        
        with allure.step("第四步：验证响应结果"):
            # 检查响应
            result = response.json()
            assert result["errorCode"] != 0, "使用空头像地址时错误码应该不为0"
            assert result["succeed"] == False, "响应succeed字段应为False"
            
            # 记录请求和响应
            allure.attach(
                f"修改头像为空字符串",
                name="请求数据",
                attachment_type=allure.attachment_type.TEXT
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            ) 