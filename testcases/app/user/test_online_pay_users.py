#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import json
import time
from utils.logger import logger
from utils.app.api.user import UserAPI

@allure.feature("用户功能")
class TestOnlinePayUsers:
    """在线付费用户列表测试"""
    
    @allure.story("在线付费用户")
    @allure.title("亲密度<200的付费用户会出现在列表中")
    @pytest.mark.smoke
    def test_online_pay_user_with_low_intimacy(self, client_factory):
        """测试亲密度<200的付费用户会出现在列表中"""
        with allure.step("第一步：登录用户8（付费用户，亲密度<200）"):
            user8_client = client_factory.get_client("user8")
            login_success = user8_client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户8登录失败"
        
        with allure.step("第二步：获取用户8的信息，确认其为付费用户"):
            user8_info_success, user8_info_response = UserAPI.get_user_info(user8_client)
            assert user8_info_success, "获取用户8信息失败"
            user8_info = user8_info_response.json()
            
            # 确认用户8是付费用户
            assert user8_info["data"]["alreadyPaying"] == True, "用户8不是付费用户，不满足测试条件"
            user8_uid = user8_info["data"]["uid"]
            user8_nick = user8_info["data"]["nick"]
            logger.info(f"确认用户8 (ID: {user8_uid}, 昵称: {user8_nick}) 为付费用户")
            
            # 将用户信息添加到报告中
            allure.attach(
                json.dumps(user8_info["data"], indent=2, ensure_ascii=False),
                name="用户8信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第三步：登录用户1（主播）"):
            anchor_client = client_factory.get_client("user1")
            anchor_login_success = anchor_client.login()
            allure.attach(str(anchor_login_success), name="主播登录结果", attachment_type=allure.attachment_type.TEXT)
            assert anchor_login_success, "主播用户1登录失败"
        
        with allure.step("第四步：获取主播用户信息，确认其为主播身份"):
            anchor_info_success, anchor_info_response = UserAPI.get_user_info(anchor_client)
            assert anchor_info_success, "获取主播用户1信息失败"
            anchor_info = anchor_info_response.json()
            
            user_roles = anchor_info["data"]["userRoles"]
            assert 2 in user_roles or 3 in user_roles, "用户1不是主播，不满足测试条件"
            logger.info(f"确认用户1 (ID: {anchor_info['data']['uid']}) 为主播")
            
            # 将主播信息添加到报告中
            allure.attach(
                json.dumps(anchor_info["data"], indent=2, ensure_ascii=False),
                name="主播用户信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        # with allure.step("第五步：等待5秒，确保登录状态已更新"):
        #     time.sleep(5)
        #     allure.attach("等待5秒完成", name="等待结果", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第六步：主播调用获取在线付费用户列表接口"):
            max_retries = 5
            retry_count = 0
            retry_delay = 3
            result = None
            
            while retry_count <= max_retries:
                success, response = UserAPI.get_online_pay_users(anchor_client)
                
                # 断言API调用成功
                assert success, f"获取在线付费用户列表失败: {response.text if response else '无响应'}"
                
                # 检查响应
                result = response.json()
                assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
                assert result["succeed"] == True, "响应succeed字段不为True"
                
                # 检查列表是否为空
                if result["data"]["list"] is not None and len(result["data"]["list"]) > 0:
                    logger.info(f"成功获取在线付费用户列表，共 {len(result['data']['list'])} 个用户")
                    allure.attach(f"重试次数: {retry_count}，获取到非空列表", name="重试结果", attachment_type=allure.attachment_type.TEXT)
                    break
                
                if retry_count < max_retries:
                    logger.info(f"在线付费用户列表为空，{retry_delay}秒后进行第 {retry_count + 1} 次重试")
                    allure.attach(f"重试次数: {retry_count}，列表为空，将在{retry_delay}秒后重试", name="重试状态", attachment_type=allure.attachment_type.TEXT)
                    time.sleep(retry_delay)
                    retry_count += 1
                else:
                    logger.warning(f"已达到最大重试次数 {max_retries}，在线付费用户列表仍为空")
                    allure.attach(f"已达到最大重试次数 {max_retries}，列表仍为空", name="重试结束", attachment_type=allure.attachment_type.TEXT)
                    break
        
        with allure.step("第七步：检查用户8是否在列表中"):
            # 检查用户8是否在列表中
            pay_users = result["data"]["list"] or []
                
            user8_found = False
            for user in pay_users:
                if user["uid"] == user8_uid:
                    user8_found = True
                    logger.info(f"用户8 (ID: {user8_uid}, 昵称: {user['nick']}) 在在线付费用户列表中")
                    break
            
            assert user8_found, f"用户8 (ID: {user8_uid}) 未在在线付费用户列表中"
            
            # 将检查结果添加到报告中
            allure.attach(
                f"用户8 (ID: {user8_uid}) {'在' if user8_found else '不在'}在线付费用户列表中",
                name="检查结果",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # 将结果以格式化的JSON形式添加到报告中
        formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
        allure.attach(
            formatted_result,
            name="在线付费用户列表(格式化)",
            attachment_type=allure.attachment_type.JSON
        )
    
    @allure.story("在线付费用户")
    @allure.title("亲密度>200的付费用户不会出现在列表中")
    @pytest.mark.smoke
    def test_online_pay_user_with_high_intimacy(self, client_factory):
        """测试亲密度>200的付费用户不会出现在列表中"""
        with allure.step("第一步：登录用户9（付费用户，亲密度>200）"):
            user9_client = client_factory.get_client("user9")
            login_success = user9_client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, "用户9登录失败"
        
        with allure.step("第二步：获取用户9的信息，确认其为付费用户"):
            user9_info_success, user9_info_response = UserAPI.get_user_info(user9_client)
            assert user9_info_success, "获取用户9信息失败"
            user9_info = user9_info_response.json()
            
            # 确认用户9是付费用户
            assert user9_info["data"]["alreadyPaying"] == True, "用户9不是付费用户，不满足测试条件"
            user9_uid = user9_info["data"]["uid"]
            user9_nick = user9_info["data"]["nick"]
            logger.info(f"确认用户9 (ID: {user9_uid}, 昵称: {user9_nick}) 为付费用户")
            
            # 将用户信息添加到报告中
            allure.attach(
                json.dumps(user9_info["data"], indent=2, ensure_ascii=False),
                name="用户9信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        with allure.step("第三步：登录用户1（主播）"):
            anchor_client = client_factory.get_client("user1")
            anchor_login_success = anchor_client.login()
            allure.attach(str(anchor_login_success), name="主播登录结果", attachment_type=allure.attachment_type.TEXT)
            assert anchor_login_success, "主播用户1登录失败"
        
        with allure.step("第四步：获取主播用户信息，确认其为主播身份"):
            anchor_info_success, anchor_info_response = UserAPI.get_user_info(anchor_client)
            assert anchor_info_success, "获取主播用户1信息失败"
            anchor_info = anchor_info_response.json()
            
            user_roles = anchor_info["data"]["userRoles"]
            assert 2 in user_roles or 3 in user_roles, "用户1不是主播，不满足测试条件"
            logger.info(f"确认用户1 (ID: {anchor_info['data']['uid']}) 为主播")
            
            # 将主播信息添加到报告中
            allure.attach(
                json.dumps(anchor_info["data"], indent=2, ensure_ascii=False),
                name="主播用户信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        # with allure.step("第五步：等待5秒，确保登录状态已更新"):
        #     time.sleep(5)
        #     allure.attach("等待5秒完成", name="等待结果", attachment_type=allure.attachment_type.TEXT)
        
        with allure.step("第六步：主播调用获取在线付费用户列表接口"):
            max_retries = 5
            retry_count = 0
            retry_delay = 3
            result = None
            
            while retry_count <= max_retries:
                success, response = UserAPI.get_online_pay_users(anchor_client)
                
                # 断言API调用成功
                assert success, f"获取在线付费用户列表失败: {response.text if response else '无响应'}"
                
                # 检查响应
                result = response.json()
                assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
                assert result["succeed"] == True, "响应succeed字段不为True"
                
                # 检查列表是否为空
                if result["data"]["list"] is not None and len(result["data"]["list"]) > 0:
                    logger.info(f"成功获取在线付费用户列表，共 {len(result['data']['list'])} 个用户")
                    allure.attach(f"重试次数: {retry_count}，获取到非空列表", name="重试结果", attachment_type=allure.attachment_type.TEXT)
                    break
                
                if retry_count < max_retries:
                    logger.info(f"在线付费用户列表为空，{retry_delay}秒后进行第 {retry_count + 1} 次重试")
                    allure.attach(f"重试次数: {retry_count}，列表为空，将在{retry_delay}秒后重试", name="重试状态", attachment_type=allure.attachment_type.TEXT)
                    time.sleep(retry_delay)
                    retry_count += 1
                else:
                    logger.warning(f"已达到最大重试次数 {max_retries}，在线付费用户列表仍为空")
                    allure.attach(f"已达到最大重试次数 {max_retries}，列表仍为空", name="重试结束", attachment_type=allure.attachment_type.TEXT)
                    break
        
        with allure.step("第七步：检查用户9是否不在列表中"):
            # 检查用户9是否不在列表中
            pay_users = result["data"]["list"] or []
            
            # 如果列表为空，则符合预期（亲密度>200的用户不应该出现在列表中）
            if not pay_users:
                logger.info(f"在线付费用户列表为空，用户9 (ID: {user9_uid}) 不在列表中，符合预期")
                allure.attach(
                    "在线付费用户列表为空，符合预期",
                    name="检查结果",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                user9_found = False
                for user in pay_users:
                    if user["uid"] == user9_uid:
                        user9_found = True
                        logger.error(f"用户9 (ID: {user9_uid}, 昵称: {user['nick']}) 不应出现在在线付费用户列表中，但实际出现了")
                        break
                
                assert not user9_found, f"用户9 (ID: {user9_uid}) 不应在在线付费用户列表中，但实际出现了"
                logger.info(f"用户9 (ID: {user9_uid}) 不在在线付费用户列表中，符合预期")
                
                # 将检查结果添加到报告中
                allure.attach(
                    f"用户9 (ID: {user9_uid}) 不在在线付费用户列表中，符合预期",
                    name="检查结果",
                    attachment_type=allure.attachment_type.TEXT
                )
        
        # 将结果以格式化的JSON形式添加到报告中
        formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
        allure.attach(
            formatted_result,
            name="在线付费用户列表(格式化)",
            attachment_type=allure.attachment_type.JSON
        ) 