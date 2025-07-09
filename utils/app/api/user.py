#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户相关API接口
"""

from utils.logger import logger
import requests
import base64
import io
from PIL import Image
import time
import os
import json


class UserAPI:
    """用户相关API接口封装"""
    
    @staticmethod
    def login(client, force=False, max_retries=3, retry_delay=5):
        """
        执行登录流程
        :param client: API客户端实例
        :param force: 是否强制重新登录
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟（秒）
        :return: 登录是否成功
        """
        # 如果已经有access_token且不强制登录，则直接返回成功
        if client.access_token and not force:
            return True
        
        import re
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 第一步：发送短信验证码
                send_sms_response = client.request(
                    method="POST",
                    url="/api/user/v1/user/login/sendSms",
                    json={
                        "phoneNum": client.user_config["phoneNumber"],
                        "phoneCode": client.user_config["phoneCode"]
                    },
                    auto_login=False  # 防止递归调用
                )
                
                # 检查发送短信是否成功
                if send_sms_response.status_code != 200:
                    logger.error(f"发送短信验证码失败: {send_sms_response.text}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                sms_result = send_sms_response.json()
                if sms_result.get("errorCode") != 0:
                    error_message = sms_result.get('errorMessage', '')
                    logger.error(f"发送短信验证码失败: {error_message}")
                    
                    # 频率限制错误，等待更长时间
                    if "Frequently" in error_message:
                        logger.warning(f"触发频率限制，等待{retry_delay*3}秒后重试...")
                        time.sleep(retry_delay * 3)
                    else:
                        time.sleep(retry_delay)
                    
                    retry_count += 1
                    continue
                
                logger.info(f"发送短信验证码成功，手机: {client.user_config['phoneCode']}-{client.user_config['phoneNumber']}")
                
                # 获取实际验证码
                get_code_response = client.request(
                    method="POST",
                    url="/api/user/v1/operate/submit",
                    json={
                        "operateName": "admin",
                        "phone": client.user_config["phoneNumber"],
                        "areaCode": client.user_config["phoneCode"],
                        "operate": "App短信验证码"
                    },
                    auto_login=False  # 防止递归调用
                )
                
                # 检查获取验证码是否成功
                if get_code_response.status_code != 200:
                    logger.error(f"获取验证码失败: {get_code_response.text}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                code_result = get_code_response.json()
                if code_result.get("errorCode") != 0 or not code_result.get("succeed"):
                    logger.error(f"获取验证码失败: {code_result.get('errorMessage')}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                # 从响应中提取验证码
                code_message = code_result["data"]["jsonValue"]
                sms_code_match = re.search(r'验证码为 \[(\d+)\]', code_message)
                if not sms_code_match:
                    logger.error(f"无法从响应中提取验证码: {code_message}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                sms_code = sms_code_match.group(1)
                logger.info(f"成功获取验证码: {sms_code}")
                
                # 第二步：执行登录
                login_response = client.request(
                    method="POST",
                    url="/api/user/v1/user/login",
                    json={
                        "bizId": 1,
                        "channel": "phone",
                        "token": client.user_config["phoneNumber"],
                        "phoneCode": client.user_config["phoneCode"],
                        "smsCode": sms_code  # 使用提取的验证码
                    },
                    auto_login=False  # 防止递归调用
                )
                
                # 检查登录是否成功
                if login_response.status_code != 200:
                    logger.error(f"登录失败: {login_response.text}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                login_result = login_response.json()
                if login_result.get("errorCode") != 0:
                    logger.error(f"登录失败: {login_result.get('errorMessage')}")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                
                # 保存token和用户信息
                client.access_token = login_result["data"]["accessToken"]
                client.user_info = login_result["data"]["userInfo"]
                
                # 更新Authorization头
                client.session.headers.update({"Authorization": client.access_token})
                
                # 获取用户身份描述
                role_description = UserAPI.get_user_role_description(client)
                
                logger.info(f"登录成功，用户ID: {client.user_info['uid']}, 昵称: {client.user_info['nick']}, 身份: {role_description}")
                return True
                
            except Exception as e:
                logger.error(f"登录过程中发生错误: {str(e)}")
                retry_count += 1
                time.sleep(retry_delay)
        
        logger.error(f"登录失败，已达到最大重试次数 {max_retries}")
        return False
    
    @staticmethod
    def modify_nick(client, new_nick):
        """
        修改用户昵称
        :param client: API客户端实例
        :param new_nick: 新昵称
        :return: (是否成功, 响应对象)
        """
        response = client.request(
            method="POST",
            url="/api/user/v1/user/modifyNick",
            json={"nick": new_nick}
        )
        
        if response.status_code != 200:
            logger.error(f"修改昵称失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"修改昵称失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if client.user_info:
            client.user_info["nick"] = new_nick
        
        logger.info(f"修改昵称成功: {new_nick}")
        return True, response
    
    @staticmethod
    def modify_profile(client, gender=None, birthday=None, country=None):
        """
        完善用户资料
        :param client: API客户端实例
        :param gender: 性别 1：男 2：女
        :param birthday: 生日，格式: YYYY-MM-DD
        :param country: 国家
        :return: (是否成功, 响应对象)
        """
        # 构建请求数据
        data = {}
        if gender is not None:
            data["gender"] = gender
        if birthday is not None:
            data["birthday"] = birthday
        if country is not None:
            data["country"] = country
        
        # 如果没有要修改的数据，返回失败
        if not data:
            logger.error("没有提供要修改的用户资料")
            return False, None
        
        response = client.request(
            method="POST",
            url="/api/user/v1/user/modifyInfo",
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"完善用户资料失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"完善用户资料失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if client.user_info:
            for key, value in data.items():
                client.user_info[key] = value
        
        logger.info(f"完善用户资料成功: {data}")
        return True, response
    
    @staticmethod
    def get_user_role_description(client):
        """
        获取用户身份描述
        根据userRoles数组判断用户身份
        :param client: API客户端实例
        :return: 用户身份描述
        """
        if not client.user_info or "userRoles" not in client.user_info:
            return "未知"
        
        roles = client.user_info["userRoles"]
        
        if not roles:
            return "普通用户"
        
        # 角色优先级: 主播 > 嘉宾 > 普通用户
        if 2 in roles:  # 2 表示主播
            return "主播"
        elif 3 in roles:  # 3 表示嘉宾
            return "嘉宾"
        else:
            return "普通用户"
    
    @staticmethod
    def get_local_photo_required():
        """
        获取是否需要本地图片
        :return: 是否需要本地图片
        """
        # 根据环境或配置决定是否需要使用本地图片
        # 这里简单返回True
        return True
    
    @staticmethod
    def load_photo_from_file(file_path):
        """
        从文件加载照片数据
        :param file_path: 照片文件路径
        :return: Base64编码的照片数据
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"照片文件不存在: {file_path}")
                return None
            
            # 使用PIL打开图片
            with Image.open(file_path) as img:
                # 检查图片大小，超过2MB时压缩
                img_bytes = io.BytesIO()
                
                # 保存为JPEG格式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                quality = 95  # 初始质量
                img.save(img_bytes, format='JPEG', quality=quality)
                
                # 如果图片过大，逐步降低质量
                while img_bytes.tell() > 2 * 1024 * 1024 and quality > 50:
                    img_bytes.seek(0)
                    img_bytes.truncate()
                    quality -= 10
                    img.save(img_bytes, format='JPEG', quality=quality)
                
                # 获取Base64编码
                img_bytes.seek(0)
                encoded_string = base64.b64encode(img_bytes.read()).decode('utf-8')
                
                return encoded_string
        
        except Exception as e:
            logger.error(f"加载照片文件失败: {str(e)}")
            return None
    
    @staticmethod
    def apply_for_anchor_certification(client, nick, avatar_data, face_data):
        """
        申请主播认证
        :param client: API客户端实例
        :param nick: 昵称
        :param avatar_data: Base64编码的头像数据
        :param face_data: Base64编码的人脸照片数据
        :return: (是否成功, 响应对象)
        """
        # 检查参数
        if not nick or not avatar_data or not face_data:
            logger.error("申请主播认证失败: 参数不完整")
            return False, None
        
        # 验证数据格式
        def is_valid_base64(data):
            try:
                # 检查是否是字符串
                if not isinstance(data, str):
                    return False
                
                # 尝试解码
                base64.b64decode(data)
                return True
            except:
                return False
        
        if not is_valid_base64(avatar_data) or not is_valid_base64(face_data):
            logger.error("申请主播认证失败: 图片数据格式不正确")
            return False, None
        
        # 第一步：上传头像
        avatar_response = client.request(
            method="POST",
            url="/api/user/v1/user/uploadAvatar",
            json={"avatarBase64": avatar_data}
        )
        
        if avatar_response.status_code != 200:
            logger.error(f"上传头像失败: {avatar_response.text}")
            return False, avatar_response
        
        avatar_result = avatar_response.json()
        if avatar_result.get("errorCode") != 0:
            logger.error(f"上传头像失败: {avatar_result.get('errorMessage')}")
            return False, avatar_response
        
        # 获取头像URL
        avatar_url = avatar_result["data"].get("fileUrl")
        if not avatar_url:
            logger.error("上传头像失败: 响应中缺少头像URL")
            return False, avatar_response
        
        logger.info(f"上传头像成功: {avatar_url}")
        
        # 第二步：上传人脸照片
        face_response = client.request(
            method="POST",
            url="/api/user/v1/user/uploadFace",
            json={"fileBase64": face_data}
        )
        
        if face_response.status_code != 200:
            logger.error(f"上传人脸照片失败: {face_response.text}")
            return False, face_response
        
        face_result = face_response.json()
        if face_result.get("errorCode") != 0:
            logger.error(f"上传人脸照片失败: {face_result.get('errorMessage')}")
            return False, face_response
        
        # 获取人脸照片URL
        face_url = face_result["data"].get("fileUrl")
        if not face_url:
            logger.error("上传人脸照片失败: 响应中缺少照片URL")
            return False, face_response
        
        logger.info(f"上传人脸照片成功: {face_url}")
        
        # 第三步：修改昵称
        nick_success, nick_response = UserAPI.modify_nick(client, nick)
        if not nick_success:
            logger.error(f"修改昵称失败，继续申请流程")
        
        # 第四步：申请主播认证
        apply_response = client.request(
            method="POST",
            url="/api/user/v1/user/applyForAnchor",
            json={
                "avatar": avatar_url,
                "face": face_url
            }
        )
        
        if apply_response.status_code != 200:
            logger.error(f"申请主播认证失败: {apply_response.text}")
            return False, apply_response
        
        apply_result = apply_response.json()
        if apply_result.get("errorCode") != 0:
            logger.error(f"申请主播认证失败: {apply_result.get('errorMessage')}")
            return False, apply_response
        
        # 返回包含头像和人脸URL的数据
        result_data = {
            "avatar": avatar_url,
            "face": face_url,
            "nick": nick
        }
        
        logger.info(f"申请主播认证成功: {result_data}")
        return True, result_data
    
    @staticmethod
    def save_base64_to_image(base64_str, file_path):
        """
        保存Base64编码的图片到文件
        :param base64_str: Base64编码的图片数据
        :param file_path: 保存路径
        :return: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 解码并保存
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(base64_str))
            
            logger.info(f"成功保存图片到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存图片失败: {str(e)}")
            return False 

    @staticmethod
    def apply_bind_agent(client, agent_id):
        """
        主播申请绑定代理
        :param client: API客户端实例
        :param agent_id: 代理用户ID
        :return: (是否成功, 响应对象)
        """
        logger.info(f"主播申请绑定代理: 代理ID={agent_id}")
        
        # 直接调用API，不检查用户身份
        response = client.request(
            method="POST",
            url="/api/workbench/v1/workbench/anchorBindAgentApply",
            json={"agentId": agent_id}
        )
        
        if response.status_code != 200:
            logger.error(f"申请绑定代理失败: HTTP {response.status_code}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"申请绑定代理失败: {result.get('errorMessage')}")
            return False, response
        
        logger.info(f"主播申请绑定代理成功: 代理ID={agent_id}")
        return True, response
    
    @staticmethod
    def is_anchor(client):
        """
        检查用户是否是主播
        :param client: API客户端实例
        :return: 是否是主播
        """
        if not client.user_info or "userRoles" not in client.user_info:
            logger.error("用户未登录或用户信息不完整")
            return False
        
        # 检查userRoles数组中是否包含主播角色
        user_roles = client.user_info.get("userRoles", [])
        
        # 根据API响应，角色是用整数表示的
        # 主播角色可能是2或其他整数，这里需要根据实际情况调整
        # 1: 普通用户
        # 2: 可能是主播
        # 如果userRoles中包含2，则认为是主播
        is_anchor = 2 in user_roles
        
        if is_anchor:
            logger.info("当前用户是主播")
        else:
            logger.info("当前用户不是主播")
        
        return is_anchor 