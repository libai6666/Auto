#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.client_factory import ClientFactory
from utils.logger import logger
from utils.app.api.user import UserAPI


def apply_for_anchors(count, base_phone="17000000000", phone_code="43", photo_path=None):
    """
    批量申请主播
    :param count: 要创建的用户数量
    :param base_phone: 基础电话号码，会递增
    :param phone_code: 国家代码
    :param photo_path: 必须，用于头像和人脸的图片文件路径
    :return: 成功申请的用户列表
    """
    # 验证必须参数
    if not photo_path:
        logger.error("必须提供照片路径！请使用 -i 参数指定本地图片文件的路径")
        return []
        
    # 检查照片文件是否存在
    if not os.path.exists(photo_path):
        logger.error(f"指定的照片文件不存在: {photo_path}")
        return []
    
    # 创建客户端工厂
    factory = ClientFactory()
    
    # 批量创建用户客户端
    logger.info(f"开始创建 {count} 个用户客户端...")
    clients = factory.create_clients(count, base_phone, phone_code)
    logger.info(f"成功创建 {len(clients)} 个用户客户端")
    
    logger.info(f"将使用指定的照片文件: {photo_path}")
    
    successful_clients = []
    
    # 对每个客户端执行操作
    for i, client in enumerate(clients):
        logger.info(f"处理第 {i+1}/{len(clients)} 个用户，手机号: {client.user_config['phoneCode']}-{client.user_config['phoneNumber']}")
        
        # 登录前添加延迟
        time.sleep(3)  # 增加到3秒
        
        # 登录
        if not client.login():
            logger.error(f"用户登录失败，跳过此用户")
            continue
        
        # 完善用户资料前添加延迟
        time.sleep(3)  # 增加到3秒
        
        # 完善用户资料（性别为女性，国家为IN，生日为2005-10-01）
        success, response = UserAPI.modify_profile(
            client,
            gender=2,         # 女性
            country="IN",     # 印度
            birthday="2005-10-01"  # 生日
        )
        
        if not success:
            logger.warning(f"完善用户资料失败，可能是已注册用户，继续尝试申请主播")
        
        # 申请主播前添加延迟
        time.sleep(3)  # 增加到3秒
        
        # 申请主播认证
        success, response = UserAPI.apply_for_anchor(client, photo_path)
        if not success:
            logger.error(f"申请主播认证失败，跳过此用户")
            continue
            
        logger.info(f"用户 {client.get_user_nick()} (ID: {client.get_user_id()}) 成功申请主播认证")
        successful_clients.append(client)
        
        # 添加延迟避免请求过于频繁
        time.sleep(5)  # 增加到5秒
    
    logger.info(f"批量操作完成，成功处理 {len(successful_clients)}/{len(clients)} 个用户")
    return successful_clients


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="批量申请主播工具")
    parser.add_argument("-c", "--count", type=int, default=1, help="要创建的用户数量")
    parser.add_argument("-b", "--base-phone", default="17000000000", help="基础电话号码，会递增")
    parser.add_argument("-p", "--phone-code", default="43", help="国家代码")
    parser.add_argument("-i", "--image", required=True, help="【必须】用于头像和人脸的图片文件路径")
    
    args = parser.parse_args()
    
    # 验证图片路径是否存在
    if not os.path.exists(args.image):
        logger.error(f"图片文件不存在: {args.image}")
        return
        
    apply_for_anchors(args.count, args.base_phone, args.phone_code, args.image)


if __name__ == "__main__":
    main()
