#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import random
import json
from utils.logger import logger
from utils.data_handler import load_yaml_data
from utils.app.api.user import UserAPI

@allure.feature("用户功能")
class TestUserProfile:
    """用户资料修改测试
       测试参数同时填生日、语言、视频地址，只能生效一个视频地址
       国家
    """
    
    @allure.story("资料修改")
    @allure.title("测试用户修改生日成功")
    @pytest.mark.smoke
    def test_modify_birthday_success(self, client_factory):
        """测试用户修改生日成功"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user1")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：加载测试数据，选择生日"):
            # 加载测试数据
            profile_data = load_yaml_data("data/app/user.yaml")["profile_test_data"]
            
            # 随机选择测试数据
            birthday = random.choice(profile_data["birthdays"])
            allure.attach(birthday, name="选择的生日", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改用户资料接口"):
            # 修改用户生日
            success, response = UserAPI.modify_profile(client, birthday=birthday)
            
            # 断言
            assert success, f"修改用户生日失败: {response.text if response else '无响应'}"
            
            # 检查响应
            result = response.json()
            assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
            assert result["succeed"] == True, "响应succeed字段不为True"
            
            # 记录请求和响应
            request_data = {
                "birthday": birthday
            }
            
            allure.attach(
                json.dumps(request_data, indent=2, ensure_ascii=False),
                name="请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第四步：验证生日修改是否生效"):
            # 调用获取用户信息接口验证生日是否修改成功
            info_success, info_response = UserAPI.get_user_info(client)
            assert info_success, "获取用户信息失败"
            
            info_result = info_response.json()
            assert info_result["errorCode"] == 0, "获取用户信息响应错误码不为0"
            assert info_result["data"]["birthday"] == birthday, f"生日修改未生效，期望: {birthday}, 实际: {info_result['data']['birthday']}"
            
            logger.info(f"生日修改验证成功，当前生日: {info_result['data']['birthday']}")
            
            # 将用户信息响应以格式化的JSON形式添加到报告中
            formatted_info = json.dumps(info_result, indent=2, ensure_ascii=False)
            allure.attach(
                formatted_info,
                name="用户信息响应(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
    
    @allure.story("资料修改")
    @allure.title("测试用户修改国家成功(用户是普通用户身份可以修改成功)")
    @pytest.mark.smoke
    def test_modify_country_success(self, client_factory):
        """测试用户修改国家成功"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user6")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：加载测试数据，选择国家"):
            # 加载测试数据
            profile_data = load_yaml_data("data/app/user.yaml")["profile_test_data"]
            
            # 随机选择测试数据
            country = random.choice(profile_data["countries"])
            allure.attach(country, name="选择的国家", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改用户资料接口"):
            # 修改用户国家
            success, response = UserAPI.modify_profile(client, country=country)
            
            # 断言
            assert success, f"修改用户国家失败: {response.text if response else '无响应'}"
            
            # 检查响应
            result = response.json()
            assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
            assert result["succeed"] == True, "响应succeed字段不为True"
            
            # 记录请求和响应
            request_data = {
                "country": country
            }
            
            allure.attach(
                json.dumps(request_data, indent=2, ensure_ascii=False),
                name="请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第四步：验证国家修改是否生效"):
            # 调用获取用户信息接口验证国家是否修改成功
            info_success, info_response = UserAPI.get_user_info(client)
            assert info_success, "获取用户信息失败"
            
            info_result = info_response.json()
            assert info_result["errorCode"] == 0, "获取用户信息响应错误码不为0"
            assert info_result["data"]["country"] == country, f"国家修改未生效，期望: {country}, 实际: {info_result['data']['country']}"
            
            logger.info(f"国家修改验证成功，当前国家: {info_result['data']['country']}")
            
            # 将用户信息响应以格式化的JSON形式添加到报告中
            formatted_info = json.dumps(info_result, indent=2, ensure_ascii=False)
            allure.attach(
                formatted_info,
                name="用户信息响应(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
    
    @allure.story("资料修改")
    @allure.title("测试用户修改语言成功")
    @pytest.mark.smoke
    def test_modify_language_success(self, client_factory):
        """测试用户修改语言成功"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user1")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：加载测试数据，选择语言"):
            # 加载测试数据
            profile_data = load_yaml_data("data/app/user.yaml")["profile_test_data"]
            
            # 随机选择测试数据
            lang = random.choice(profile_data["languages"])
            allure.attach(lang, name="选择的语言", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改用户资料接口"):
            # 修改用户语言
            success, response = UserAPI.modify_profile(client, lang=lang)
            
            # 断言
            assert success, f"修改用户语言失败: {response.text if response else '无响应'}"
            
            # 检查响应
            result = response.json()
            assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
            assert result["succeed"] == True, "响应succeed字段不为True"
            
            # 记录请求和响应
            request_data = {
                "lang": lang
            }
            
            allure.attach(
                json.dumps(request_data, indent=2, ensure_ascii=False),
                name="请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第四步：验证语言修改是否生效"):
            # 调用获取用户信息接口验证语言是否修改成功
            info_success, info_response = UserAPI.get_user_info(client)
            assert info_success, "获取用户信息失败"
            
            info_result = info_response.json()
            assert info_result["errorCode"] == 0, "获取用户信息响应错误码不为0"
            assert info_result["data"]["lang"] == lang, f"语言修改未生效，期望: {lang}, 实际: {info_result['data']['lang']}"
            
            logger.info(f"语言修改验证成功，当前语言: {info_result['data']['lang']}")
            
            # 将用户信息响应以格式化的JSON形式添加到报告中
            formatted_info = json.dumps(info_result, indent=2, ensure_ascii=False)
            allure.attach(
                formatted_info,
                name="用户信息响应(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
    
    @allure.story("资料修改")
    @allure.title("测试用户修改视频地址成功")
    @pytest.mark.smoke
    def test_modify_video_url_success(self, client_factory):
        """测试用户修改视频地址成功"""
        with allure.step("第一步：获取测试客户端并登录"):
            # 获取测试客户端
            client = client_factory.get_client("user1")
            
            # 确保登录
            login_success = client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户登录失败"
        
        with allure.step("第二步：加载测试数据，选择视频地址"):
            # 加载测试数据
            profile_data = load_yaml_data("data/app/user.yaml")["profile_test_data"]
            
            # 随机选择测试数据
            video_url = random.choice(profile_data["video_urls"])
            allure.attach(video_url, name="选择的视频地址", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第三步：调用修改用户资料接口"):
            # 修改用户视频地址
            success, response = UserAPI.modify_profile(client, videoUrl=video_url)
            
            # 断言
            assert success, f"修改用户视频地址失败: {response.text if response else '无响应'}"
            
            # 检查响应
            result = response.json()
            assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
            assert result["succeed"] == True, "响应succeed字段不为True"
            
            # 记录请求和响应
            request_data = {
                "videoUrl": video_url
            }
            
            allure.attach(
                json.dumps(request_data, indent=2, ensure_ascii=False),
                name="请求数据",
                attachment_type=allure.attachment_type.JSON
            )
            allure.attach(
                json.dumps(result, indent=2, ensure_ascii=False),
                name="响应数据(格式化)",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第四步：验证视频地址修改是否生效"):
            # 调用获取用户信息接口验证视频地址是否修改成功
            info_success, info_response = UserAPI.get_user_info(client)
            assert info_success, "获取用户信息失败"
            
            info_result = info_response.json()
            assert info_result["errorCode"] == 0, "获取用户信息响应错误码不为0"
            assert info_result["data"]["videoUrl"] == video_url, f"视频地址修改未生效，期望: {video_url}, 实际: {info_result['data']['videoUrl']}"
            
            logger.info(f"视频地址修改验证成功，当前视频地址: {info_result['data']['videoUrl']}")
            
            # 将用户信息响应以格式化的JSON形式添加到报告中
            formatted_info = json.dumps(info_result, indent=2, ensure_ascii=False)
            allure.attach(
                formatted_info,
                name="用户信息响应(格式化)",
                attachment_type=allure.attachment_type.JSON
            )