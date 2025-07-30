#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import sys
import os
import random

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.client_factory import ClientFactory
from utils.logger import logger
from utils.app.api.user import UserAPI
from utils.data_handler import load_config


def get_random_urls():
    """
    从user.yaml配置中随机获取一个有效的头像URL和面部照片URL
    :return: (随机头像URL或None, 随机面部照片URL或None)
    """
    try:
        # 加载user.yaml配置
        from utils.data_handler import load_yaml_data
        user_data = load_yaml_data("data/app/user.yaml")
        if not user_data:
            logger.error("无法加载user.yaml配置文件")
            return None, None
            
        # 获取有效头像列表
        valid_avatars = user_data.get("avatar_test_data", {}).get("valid_avatars", [])
        if not valid_avatars:
            logger.error("未在user.yaml中找到有效的头像URL")
            return None, None
            
        # 获取有效面部照片列表
        valid_faces = user_data.get("avatar_test_data", {}).get("valid_face_urls", [])
        if not valid_faces:
            logger.error("未在user.yaml中找到有效的面部照片URL")
            return None, None
            
        # 随机选择一个头像URL和面部照片URL
        avatar_url = random.choice(valid_avatars)
        face_url = random.choice(valid_faces)
        
        logger.info(f"从user.yaml中随机选择头像URL: {avatar_url}")
        logger.info(f"从user.yaml中随机选择面部照片URL: {face_url}")
        
        return avatar_url, face_url
    except Exception as e:
        logger.error(f"获取随机URL时出错: {str(e)}")
        return None, None


def apply_for_anchors(count, base_phone="17000000000", phone_code="43", photo_path=None, use_yaml_avatar=True):
    """
    批量申请主播
    :param count: 要创建的用户数量
    :param base_phone: 基础电话号码，会递增
    :param phone_code: 国家代码
    :param photo_path: 用于头像和人脸的图片文件路径（可选，默认使用配置文件中的URL）
    :param use_yaml_avatar: 是否使用user.yaml中的头像URL和面部照片URL，默认为True
    :return: 成功申请的用户列表
    """
    # 如果提供了照片路径，则优先使用本地照片
    if photo_path:
        use_yaml_avatar = False
        
    # 如果使用yaml中的头像和面部照片，获取随机URL
    avatar_url = None
    face_url = None
    if use_yaml_avatar:
        avatar_url, face_url = get_random_urls()
        if not avatar_url or not face_url:
            logger.error("无法从user.yaml获取有效的头像URL或面部照片URL，请检查配置")
            return []
    # 否则检查照片文件是否存在
    elif not os.path.exists(photo_path):
        logger.error(f"指定的照片文件不存在: {photo_path}")
        return []
    
    # 创建客户端工厂
    factory = ClientFactory()
    
    # 批量创建用户客户端
    logger.info(f"开始创建 {count} 个用户客户端...")
    clients = factory.create_clients(count, base_phone, phone_code)
    logger.info(f"成功创建 {len(clients)} 个用户客户端")
    
    if use_yaml_avatar:
        logger.info(f"将使用user.yaml中的头像URL: {avatar_url}")
        logger.info(f"将使用user.yaml中的面部照片URL: {face_url}")
    else:
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
        
        # 如果使用yaml中的头像和面部照片
        if use_yaml_avatar:
            # 设置头像前添加延迟
            time.sleep(3)
            
            # 设置头像
            avatar_success, avatar_response = UserAPI.modify_avatar(client, avatar_url)
            if not avatar_success:
                logger.error(f"设置头像失败，跳过此用户")
                continue
            
            logger.info(f"成功设置头像: {avatar_url}")
            
            # 申请主播前添加延迟
            time.sleep(3)
            
            # 构造用户昵称（与apply_for_anchor方法中的逻辑一致）
            uid = client.get_user_id()
            uid_last_three = str(uid)[-3:]
            try:
                from pypinyin import lazy_pinyin
                
                def number_to_chinese(number):
                    chinese_dict = {
                        0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
                        5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
                    }
                    return chinese_dict.get(number, '零')
                    
                pinyin_list = []
                for digit in uid_last_three:
                    chinese_digit = number_to_chinese(int(digit))
                    pinyin = ''.join(lazy_pinyin(chinese_digit))
                    pinyin_list.append(pinyin)
                
                nick = "A" + ''.join(pinyin_list)
            except ImportError:
                logger.warning("未安装pypinyin模块，使用简单昵称")
                nick = "A" + uid_last_three
                
            # 直接调用apply_for_anchor_certification方法，传入头像URL和面部照片URL
            success, response = UserAPI.apply_for_anchor_certification(
                client, 
                nick, 
                "", # 这里不需要传递base64数据，因为我们直接使用URL
                ""  # 这里不需要传递base64数据，因为我们直接使用URL
            )
            
            if success:
                # 申请主播认证成功后，手动调用修改头像和申请主播认证
                apply_response = client.request(
                    method="POST",
                    url="/api/user/v1/user/applyForAnchor",
                    json={
                        "avatar": avatar_url,
                        "face": face_url
                    }
                )
                
                apply_result = apply_response.json()
                if apply_result.get("errorCode") != 0:
                    logger.error(f"申请主播认证失败: {apply_result.get('errorMessage')}")
                    success = False
                else:
                    logger.info(f"成功申请主播认证，使用头像URL: {avatar_url} 和面部照片URL: {face_url}")
        else:
            # 申请主播前添加延迟
            time.sleep(3)
            
            # 申请主播认证（使用本地照片）
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
    parser.add_argument("-i", "--image", help="用于头像和人脸的图片文件路径（可选，默认使用配置文件中的URL）")
    parser.add_argument("-l", "--local-only", action="store_true", help="仅使用本地图片文件，不使用配置中的URL（需要与-i参数一起使用）")
    
    args = parser.parse_args()
    
    # 确定是否使用YAML中的头像和面部照片
    use_yaml_avatar = not args.local_only
    
    # 如果指定了仅使用本地图片但没有提供图片路径
    if args.local_only and not args.image:
        logger.error("使用--local-only选项时必须提供图片文件路径(-i/--image)")
        return
    
    # 如果指定了使用本地图片，验证图片路径是否存在
    if args.image and not os.path.exists(args.image):
        logger.error(f"图片文件不存在: {args.image}")
        return
        
    apply_for_anchors(args.count, args.base_phone, args.phone_code, args.image, use_yaml_avatar)


if __name__ == "__main__":
    main()
