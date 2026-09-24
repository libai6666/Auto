#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
访客批量申请家族脚本
功能：批量创建访客用户，申请加入指定家族，家族长自动同意申请
示例：python scripts/batch_apply_tribe.py 
-c <访客数量> -t <家族ID> -p <家族长手机号> --phone-code <区号>
"""

import argparse
import time
import sys
import os
import uuid

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import APIClient
from utils.client_factory import ClientFactory
from utils.logger import logger


class GuestClient(APIClient):
    """
    访客用户客户端，用于访客登录
    """
    def __init__(self, base_url=None, timeout=None):
        super().__init__(base_url, timeout)
        self.access_token = None
        self.user_info = None
        
        # 设置公共头
        common_headers = {
            "d": "111",
            "p": "1",
            "v": "5.8.1",
            "l": "zh-en",
            "appName": "duoo",
            "bizId": "6",
            "Content-Type": "application/json"
        }
        self.session.headers.update(common_headers)
    
    def guest_login(self):
        """
        访客登录
        :return: 登录是否成功
        """
        # 生成随机UUID作为token
        guest_token = str(uuid.uuid4())
        
        login_data = {
            "bizId": 6,
            "channel": "guest",
            "token": guest_token,
            "phoneCode": None,
            "smsCode": None,
            "password": None,
            "installReferrer": None,
            "inviteCode": None,
            "limitedUseAppCheckToken": None,
            "anchorId": 0,
            "shareId": 0
        }
        
        try:
            response = self.request(
                method="POST",
                url="/api/user/v1/user/login",
                json=login_data
            )
            
            if response.status_code != 200:
                logger.error(f"访客登录失败: {response.text}")
                return False
            
            result = response.json()
            if result.get("errorCode") != 0:
                logger.error(f"访客登录失败: {result.get('errorMessage')}")
                return False
            
            # 保存token和用户信息
            self.access_token = result["data"]["accessToken"]
            self.user_info = result["data"]["userInfo"]
            
            # 更新Authorization头
            self.session.headers.update({"Authorization": self.access_token})
            
            logger.info(f"访客登录成功，用户ID: {self.user_info['uid']}, 昵称: {self.user_info.get('nick', 'Guest')}")
            return True
            
        except Exception as e:
            logger.error(f"访客登录异常: {str(e)}")
            return False
    
    def get_user_id(self):
        """获取用户ID"""
        return self.user_info["uid"] if self.user_info else None
    
    def apply_tribe(self, tribe_id):
        """
        申请加入家族
        :param tribe_id: 家族ID
        :return: (是否成功, 响应对象)
        """
        apply_data = {
            "tribeId": tribe_id,
            "apply": 1  # 1: 申请加入
        }
        
        try:
            response = self.request(
                method="POST",
                url="/api/live/v1/tribe/room/member/apply",
                json=apply_data
            )
            
            if response.status_code != 200:
                logger.error(f"申请家族失败: {response.text}")
                return False, response
            
            result = response.json()
            if result.get("errorCode") != 0:
                logger.error(f"申请家族失败: {result.get('errorMessage')}")
                return False, response
            
            logger.info(f"用户 {self.get_user_id()} 成功申请加入家族 {tribe_id}")
            return True, response
            
        except Exception as e:
            logger.error(f"申请家族异常: {str(e)}")
            return False, None


def approve_member(leader_client, uid, status=1):
    """
    家族长同意/拒绝成员申请
    :param leader_client: 家族长客户端
    :param uid: 申请用户ID
    :param status: 1：审核通过、2：审核不通过、3：同意退会、4：拒绝退会、5：踢出家族
    :return: (是否成功, 响应对象)
    """
    approve_data = {
        "uid": uid,
        "status": status
    }
    
    try:
        response = leader_client.request(
            method="POST",
            url="/api/live/v1/tribe/room/member/approve",
            json=approve_data
        )
        
        if response.status_code != 200:
            logger.error(f"审核成员申请失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"审核成员申请失败: {result.get('errorMessage')}")
            return False, response
        
        status_desc = {1: "通过", 2: "拒绝", 3: "同意退会", 4: "拒绝退会", 5: "踢出"}
        logger.info(f"家族长已{status_desc.get(status, '处理')}用户 {uid} 的申请")
        return True, response
        
    except Exception as e:
        logger.error(f"审核成员申请异常: {str(e)}")
        return False, None


def batch_apply_tribe(count, tribe_id, leader_phone, leader_phone_code="86"):
    """
    批量访客申请家族
    :param count: 访客数量
    :param tribe_id: 家族ID
    :param leader_phone: 家族长手机号
    :param leader_phone_code: 家族长手机区号
    :return: 成功申请的用户列表
    """
    # 创建家族长客户端并登录
    logger.info(f"正在登录家族长账号: {leader_phone_code}-{leader_phone}")
    factory = ClientFactory()
    leader_client = factory.create_custom_client(leader_phone, leader_phone_code, "家族长", auto_heartbeat=False)
    
    if not leader_client.login():
        logger.error("家族长登录失败，无法继续")
        return []
    
    logger.info(f"家族长登录成功，用户ID: {leader_client.get_user_id()}")
    
    successful_guests = []
    
    for i in range(count):
        logger.info(f"\n========== 处理第 {i+1}/{count} 个访客 ==========")
        
        # 第一步：访客登录
        guest = GuestClient()
        if not guest.guest_login():
            logger.error(f"第 {i+1} 个访客登录失败，跳过")
            time.sleep(1)
            continue
        
        guest_uid = guest.get_user_id()
        
        # 第二步：申请加入家族
        time.sleep(1)  # 避免请求过于频繁
        success, _ = guest.apply_tribe(tribe_id)
        if not success:
            logger.error(f"第 {i+1} 个访客申请家族失败，跳过")
            time.sleep(1)
            continue
        
        # 第三步：家族长同意申请
        time.sleep(1)
        success, _ = approve_member(leader_client, guest_uid, status=1)
        if not success:
            logger.error(f"家族长同意第 {i+1} 个访客申请失败")
            time.sleep(1)
            continue
        
        successful_guests.append({
            "index": i + 1,
            "uid": guest_uid
        })
        
        logger.info(f"第 {i+1} 个访客成功加入家族！")
        time.sleep(2)  # 每个完整流程后延迟
    
    logger.info(f"\n========== 批量操作完成 ==========")
    logger.info(f"成功处理 {len(successful_guests)}/{count} 个访客")
    
    if successful_guests:
        logger.info("成功加入家族的用户列表:")
        for guest in successful_guests:
            logger.info(f"  - 第{guest['index']}个访客, UID: {guest['uid']}")
    
    return successful_guests


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="访客批量申请家族工具")
    parser.add_argument("-c", "--count", type=int, required=True, help="访客数量")
    parser.add_argument("-t", "--tribe-id", type=int, required=True, help="家族ID")
    parser.add_argument("-p", "--phone", required=True, help="家族长手机号")
    parser.add_argument("--phone-code", default="86", help="家族长手机区号，默认86")
    
    args = parser.parse_args()
    
    if args.count <= 0:
        logger.error("访客数量必须大于0")
        return
    
    if args.tribe_id <= 0:
        logger.error("家族ID必须大于0")
        return
    
    batch_apply_tribe(args.count, args.tribe_id, args.phone, args.phone_code)


if __name__ == "__main__":
    main()
