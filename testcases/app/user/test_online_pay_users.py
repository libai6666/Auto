#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import allure
import json
import time
from utils.logger import logger
from utils.app.api.user import UserAPI
from utils.general_tools import find_user_by_description_pattern

@allure.feature("用户功能")
class TestOnlinePayUsers:
    """在线付费用户列表测试"""
    
    @allure.story("在线付费用户")
    @allure.title("亲密度<200的付费用户会出现在列表中")
    @pytest.mark.smoke
    def test_online_pay_user_with_low_intimacy(self, client_factory):
        """测试亲密度<200的付费用户会出现在列表中"""
        # 查找亲密度<200的付费用户
        low_intimacy_user_id, low_intimacy_user_desc = find_user_by_description_pattern(
            r"付费用户.*小于200亲密"
        )
        assert low_intimacy_user_id, "未找到符合条件的低亲密度付费用户，请检查users.yaml配置"
        
        with allure.step(f"第一步：登录低亲密度付费用户（{low_intimacy_user_desc}）"):
            low_intimacy_client = client_factory.get_client(low_intimacy_user_id)
            login_success = low_intimacy_client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, f"{low_intimacy_user_desc}登录失败"
        
        with allure.step("第二步：获取低亲密度付费用户信息，确认其为付费用户"):
            user_info_success, user_info_response = UserAPI.get_user_info(low_intimacy_client)
            assert user_info_success, f"获取{low_intimacy_user_desc}信息失败"
            user_info = user_info_response.json()
            
            # 确认是付费用户
            assert user_info["data"]["alreadyPaying"] == True, f"{low_intimacy_user_desc}不是付费用户，不满足测试条件"
            test_user_uid = user_info["data"]["uid"]
            test_user_nick = user_info["data"]["nick"]
            logger.info(f"确认{low_intimacy_user_desc} (ID: {test_user_uid}, 昵称: {test_user_nick}) 为付费用户")
            
            # 将用户信息添加到报告中
            allure.attach(
                json.dumps(user_info["data"], indent=2, ensure_ascii=False),
                name="低亲密度付费用户信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        # 查找主播用户
        anchor_user_id, anchor_user_desc = find_user_by_description_pattern(r"主播")
        assert anchor_user_id, "未找到主播用户，请检查users.yaml配置"
        
        with allure.step(f"第三步：登录主播（{anchor_user_desc}）"):
            anchor_client = client_factory.get_client(anchor_user_id)
            anchor_login_success = anchor_client.login()
            allure.attach(str(anchor_login_success), name="主播登录结果", attachment_type=allure.attachment_type.TEXT)
            assert anchor_login_success, f"{anchor_user_desc}登录失败"
        
        with allure.step("第四步：获取主播用户信息，确认其为主播身份"):
            anchor_info_success, anchor_info_response = UserAPI.get_user_info(anchor_client)
            assert anchor_info_success, f"获取{anchor_user_desc}信息失败"
            anchor_info = anchor_info_response.json()
            
            user_roles = anchor_info["data"]["userRoles"]
            assert 2 in user_roles or 3 in user_roles, f"{anchor_user_desc}不是主播，不满足测试条件"
            logger.info(f"确认{anchor_user_desc} (ID: {anchor_info['data']['uid']}) 为主播")
            
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
            retry_delay = 10
            result = None
            test_user_found = False
            
            while retry_count <= max_retries:
                success, response = UserAPI.get_online_pay_users(anchor_client)
                
                # 断言API调用成功
                assert success, f"获取在线付费用户列表失败: {response.text if response else '无响应'}"
                
                # 检查响应
                result = response.json()
                assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
                assert result["succeed"] == True, "响应succeed字段不为True"
                
                # 获取用户列表
                pay_users = result["data"]["list"] or []
                
                # 检查测试用户是否在列表中
                for user in pay_users:
                    if user["uid"] == test_user_uid:
                        test_user_found = True
                        logger.info(f"测试用户 (ID: {test_user_uid}, 昵称: {user['nick']}) 在在线付费用户列表中")
                        break
                
                if test_user_found:
                    logger.info(f"成功找到测试用户，在线付费用户列表共 {len(pay_users)} 个用户")
                    allure.attach(f"重试次数: {retry_count}，在列表中找到测试用户", name="重试结果", attachment_type=allure.attachment_type.TEXT)
                    break
                
                if retry_count < max_retries:
                    logger.info(f"未找到测试用户，{retry_delay}秒后进行第 {retry_count + 1} 次重试")
                    allure.attach(f"重试次数: {retry_count}，未找到测试用户，将在{retry_delay}秒后重试", name="重试状态", attachment_type=allure.attachment_type.TEXT)
                    time.sleep(retry_delay)
                    retry_count += 1
                else:
                    logger.warning(f"已达到最大重试次数 {max_retries}，未找到测试用户")
                    allure.attach(f"已达到最大重试次数 {max_retries}，未找到测试用户", name="重试结束", attachment_type=allure.attachment_type.TEXT)
                    break
        
        with allure.step("第七步：检查低亲密度付费用户是否在列表中"):
            # 断言测试用户在列表中
            assert test_user_found, f"低亲密度付费用户 (ID: {test_user_uid}) 未在在线付费用户列表中"
            
            # 将检查结果添加到报告中
            allure.attach(
                f"低亲密度付费用户 (ID: {test_user_uid}) {'在' if test_user_found else '不在'}在线付费用户列表中",
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
        # 查找亲密度>200的付费用户
        high_intimacy_user_id, high_intimacy_user_desc = find_user_by_description_pattern(
            r"付费用户.*大于200亲密"
        )
        assert high_intimacy_user_id, "未找到符合条件的高亲密度付费用户，请检查users.yaml配置"
        
        with allure.step(f"第一步：登录高亲密度付费用户（{high_intimacy_user_desc}）"):
            high_intimacy_client = client_factory.get_client(high_intimacy_user_id)
            login_success = high_intimacy_client.login()
            allure.attach(str(login_success), name="登录结果", attachment_type=allure.attachment_type.TEXT)
            assert login_success, f"{high_intimacy_user_desc}登录失败"
        
        with allure.step("第二步：获取高亲密度付费用户信息，确认其为付费用户"):
            user_info_success, user_info_response = UserAPI.get_user_info(high_intimacy_client)
            assert user_info_success, f"获取{high_intimacy_user_desc}信息失败"
            user_info = user_info_response.json()
            
            # 确认是付费用户
            assert user_info["data"]["alreadyPaying"] == True, f"{high_intimacy_user_desc}不是付费用户，不满足测试条件"
            test_user_uid = user_info["data"]["uid"]
            test_user_nick = user_info["data"]["nick"]
            logger.info(f"确认{high_intimacy_user_desc} (ID: {test_user_uid}, 昵称: {test_user_nick}) 为付费用户")
            
            # 将用户信息添加到报告中
            allure.attach(
                json.dumps(user_info["data"], indent=2, ensure_ascii=False),
                name="高亲密度付费用户信息",
                attachment_type=allure.attachment_type.JSON
            )
        
        # 查找主播用户
        anchor_user_id, anchor_user_desc = find_user_by_description_pattern(r"主播")
        assert anchor_user_id, "未找到主播用户，请检查users.yaml配置"
        
        with allure.step(f"第三步：登录主播（{anchor_user_desc}）"):
            anchor_client = client_factory.get_client(anchor_user_id)
            anchor_login_success = anchor_client.login()
            allure.attach(str(anchor_login_success), name="主播登录结果", attachment_type=allure.attachment_type.TEXT)
            assert anchor_login_success, f"{anchor_user_desc}登录失败"
        
        with allure.step("第四步：获取主播用户信息，确认其为主播身份"):
            anchor_info_success, anchor_info_response = UserAPI.get_user_info(anchor_client)
            assert anchor_info_success, f"获取{anchor_user_desc}信息失败"
            anchor_info = anchor_info_response.json()
            
            user_roles = anchor_info["data"]["userRoles"]
            assert 2 in user_roles or 3 in user_roles, f"{anchor_user_desc}不是主播，不满足测试条件"
            logger.info(f"确认{anchor_user_desc} (ID: {anchor_info['data']['uid']}) 为主播")
            
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
            max_retries = 2
            retry_count = 0
            retry_delay = 10
            result = None
            test_user_found = False
            
            while retry_count <= max_retries:
                success, response = UserAPI.get_online_pay_users(anchor_client)
                
                # 断言API调用成功
                assert success, f"获取在线付费用户列表失败: {response.text if response else '无响应'}"
                
                # 检查响应
                result = response.json()
                assert result["errorCode"] == 0, f"响应错误码不为0: {result['errorMessage']}"
                assert result["succeed"] == True, "响应succeed字段不为True"
                
                # 获取用户列表
                pay_users = result["data"]["list"] or []
                
                # 检查测试用户是否在列表中
                for user in pay_users:
                    if user["uid"] == test_user_uid:
                        test_user_found = True
                        logger.error(f"测试用户 (ID: {test_user_uid}, 昵称: {user['nick']}) 不应出现在在线付费用户列表中，但实际出现了")
                        break
                
                # 如果找到了测试用户或获取到了非空列表，则退出重试
                if test_user_found or pay_users:
                    logger.info(f"成功获取在线付费用户列表，共 {len(pay_users)} 个用户")
                    if test_user_found:
                        allure.attach(f"重试次数: {retry_count}，在列表中找到了测试用户（不符合预期）", name="重试结果", attachment_type=allure.attachment_type.TEXT)
                    else:
                        allure.attach(f"重试次数: {retry_count}，获取到非空列表，测试用户不在列表中", name="重试结果", attachment_type=allure.attachment_type.TEXT)
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
        
        with allure.step("第七步：检查高亲密度付费用户是否不在列表中"):
            # 断言测试用户不在列表中
            assert not test_user_found, f"{high_intimacy_user_desc} (ID: {test_user_uid}) 不应在在线付费用户列表中，但实际出现了"
            
            # 将检查结果添加到报告中
            pay_users = result["data"]["list"] or []
            if not pay_users:
                logger.info(f"在线付费用户列表为空，{high_intimacy_user_desc} (ID: {test_user_uid}) 不在列表中，符合预期")
                allure.attach(
                    "在线付费用户列表为空，符合预期",
                    name="检查结果",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                logger.info(f"{high_intimacy_user_desc} (ID: {test_user_uid}) 不在在线付费用户列表中，符合预期")
                allure.attach(
                    f"{high_intimacy_user_desc} (ID: {test_user_uid}) 不在在线付费用户列表中，符合预期",
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