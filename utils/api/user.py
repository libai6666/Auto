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
        # 构建请求参数
        profile_data = {}
        if gender is not None:
            profile_data["gender"] = gender
        if birthday is not None:
            profile_data["birthday"] = birthday
        if country is not None:
            profile_data["country"] = country
            
        # 如果没有任何参数，直接返回成功
        if not profile_data:
            logger.warning("没有提供任何资料更新参数")
            return True, None
            
        response = client.request(
            method="POST",
            url="/api/user/v1/user/modifyProfile",
            json=profile_data
        )
        
        if response.status_code != 200:
            logger.error(f"完善用户资料失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"完善用户资料失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if client.user_info and result.get("data") and result["data"].get("userInfo"):
            updated_info = result["data"]["userInfo"]
            # 更新性别
            if "gender" in profile_data and "gender" in updated_info:
                client.user_info["gender"] = updated_info["gender"]
            # 更新生日
            if "birthday" in profile_data and "birthday" in updated_info:
                client.user_info["birthday"] = updated_info["birthday"]
            # 更新国家
            if "country" in profile_data and "country" in updated_info:
                client.user_info["country"] = updated_info["country"]
        
        logger.info(f"完善用户资料成功: {profile_data}")
        return True, response
    
    @staticmethod
    def get_user_role_description(client):
        """
        获取用户身份描述
        根据userRoles数组判断用户身份：
        - 只有1：用户
        - 包含2：主播
        - 包含4：代理
        - 同时包含2和4：主播和代理
        :param client: API客户端实例
        :return: 用户身份描述
        """
        if not client.user_info or "userRoles" not in client.user_info:
            return "未知"
        
        roles = client.user_info["userRoles"]
        
        # 检查是否为主播和代理
        if 2 in roles and 4 in roles:
            return "主播和代理"
        # 检查是否为主播
        elif 2 in roles:
            return "主播"
        # 检查是否为代理
        elif 4 in roles:
            return "代理"
        # 默认为普通用户
        elif 1 in roles:
            return "用户"
        else:
            return "未知"
    
    @staticmethod
    def get_local_photo_required():
        """
        提示需要本地照片的方法，替代原来的随机照片生成方法
        :return: None 并记录错误日志
        """
        logger.error("必须提供本地照片路径！请使用 -i 参数指定本地图片文件的路径，如：-i data/anchor_image/auto.jpg")
        return None
    
    @staticmethod
    def load_photo_from_file(file_path):
        """
        从文件加载照片，返回原始图片数据
        :param file_path: 图片文件路径
        :return: 原始图片数据或None（如果加载失败）
        """
        if not file_path:
            logger.error("未提供照片文件路径")
            return None
            
        if not os.path.exists(file_path):
            logger.error(f"照片文件不存在: {file_path}")
            return None
            
        try:
            logger.info(f"正在从文件加载照片: {file_path}")
            with open(file_path, 'rb') as f:
                file_data = f.read()
                logger.info(f"文件读取成功，原始大小: {len(file_data)/1024:.2f} KB")
                
                # 读取图片信息，但不修改图片数据
                try:
                    img = Image.open(io.BytesIO(file_data))
                    logger.info(f"图片格式: {img.format}, 大小: {img.size}, 模式: {img.mode}")
                except Exception as e:
                    logger.warning(f"无法读取图片信息: {str(e)}")
                
                # 直接返回原始数据，不做任何转换
                logger.info(f"直接使用原始图片数据，大小: {len(file_data)/1024:.2f} KB")
                return file_data
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            return None
        except PermissionError:
            logger.error(f"没有权限读取文件: {file_path}")
            return None
        except Exception as e:
            logger.error(f"加载图片文件失败: {str(e)}")
            return None
    
    @staticmethod
    def apply_for_anchor_certification(client, nick, avatar_data, face_data):
        """
        申请主播认证
        :param client: UserClient实例
        :param nick: 昵称
        :param avatar_data: 头像图片数据
        :param face_data: 人脸图片数据
        :return: (是否成功, 响应对象)
        """
        url = "/api/user/v1/user/anchorCertificationApply"
        
        # 保存头像和人脸照片到临时目录，便于查看
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                "data", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 不做任何图片处理，直接使用原始数据
        logger.info(f"直接使用原始图片数据，头像大小: {len(avatar_data)/1024:.2f}KB, 人脸大小: {len(face_data)/1024:.2f}KB")
        
        # 保存原始二进制图片到临时文件
        timestamp = int(time.time())
        avatar_file = os.path.join(temp_dir, f"avatar_{timestamp}.jpg")
        face_file = os.path.join(temp_dir, f"face_{timestamp}.jpg")
        
        with open(avatar_file, 'wb') as f:
            f.write(avatar_data)
        logger.info(f"已保存头像图片到: {avatar_file}")
        
        with open(face_file, 'wb') as f:
            f.write(face_data)
        logger.info(f"已保存人脸图片到: {face_file}")
        
        # 构造请求数据
        avatar_base64 = base64.b64encode(avatar_data).decode('utf-8')
        face_base64 = base64.b64encode(face_data).decode('utf-8')
        
        # 保存base64编码后的图片（主要用于调试）
        avatar_base64_file = os.path.join(temp_dir, f"avatar_base64_{timestamp}.txt")
        with open(avatar_base64_file, 'w') as f:
            f.write(avatar_base64[:100] + "..." if len(avatar_base64) > 100 else avatar_base64)
        logger.info(f"已保存头像base64编码（截断）到: {avatar_base64_file}")
        
        # 检查base64数据大小
        avatar_base64_size = len(avatar_base64) / 1024
        face_base64_size = len(face_base64) / 1024
        
        if avatar_base64_size > 500 or face_base64_size > 500:
            logger.warning(f"Base64编码数据过大: 头像 {avatar_base64_size:.2f}KB, 人脸 {face_base64_size:.2f}KB")
            logger.warning("大图片可能导致请求失败，建议使用更小的图片")
        
        payload = {
            "nick": nick,
            "avatar": avatar_base64,
            "face": face_base64
        }
        
        logger.info(f"发送主播认证请求，昵称: {nick}, 图片大小: 头像 {len(avatar_data)/1024:.2f}KB, 人脸 {len(face_data)/1024:.2f}KB")
        
        try:
            response = client.post(url, json=payload)
            
            # 更详细地记录响应
            logger.info(f"服务器响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            # 尝试解析JSON
            try:
                json_response = response.json()
                if response.status_code == 200 and (json_response.get("code") == 0 or json_response.get("errorCode") == 0):
                    logger.info("主播认证申请成功")
                    
                    # 提取并记录返回的图片URL
                    data = json_response.get("data", {})
                    avatar_url = None
                    face_url = None
                    
                    if "avatar" in data:
                        avatar_url = data.get("avatar")
                        logger.info(f"服务器返回的头像URL: {avatar_url}")
                    else:
                        logger.warning("服务器响应中没有头像URL")
                        
                    if "face" in data:
                        face_url = data.get("face")
                        logger.info(f"服务器返回的人脸URL: {face_url}")
                    else:
                        logger.warning("服务器响应中没有人脸URL")
                    
                    # 保存返回的URL信息到文件
                    url_info_file = os.path.join(temp_dir, f"photo_urls_{timestamp}.json")
                    with open(url_info_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "timestamp": timestamp,
                            "avatar_url": avatar_url,
                            "face_url": face_url,
                            "full_response": json_response
                        }, f, ensure_ascii=False, indent=2)
                    logger.info(f"已保存照片URL信息到: {url_info_file}")
                    
                    # 尝试下载图片
                    if avatar_url:
                        try:
                            avatar_download_path = os.path.join(temp_dir, f"downloaded_avatar_{timestamp}.jpg")
                            avatar_res = requests.get(avatar_url, timeout=10)
                            if avatar_res.status_code == 200:
                                with open(avatar_download_path, 'wb') as f:
                                    f.write(avatar_res.content)
                                logger.info(f"已下载头像到: {avatar_download_path}")
                            else:
                                logger.warning(f"下载头像失败，状态码: {avatar_res.status_code}")
                        except Exception as e:
                            logger.warning(f"下载头像时出错: {str(e)}")
                    
                    if face_url:
                        try:
                            face_download_path = os.path.join(temp_dir, f"downloaded_face_{timestamp}.jpg")
                            face_res = requests.get(face_url, timeout=10)
                            if face_res.status_code == 200:
                                with open(face_download_path, 'wb') as f:
                                    f.write(face_res.content)
                                logger.info(f"已下载人脸到: {face_download_path}")
                            else:
                                logger.warning(f"下载人脸失败，状态码: {face_res.status_code}")
                        except Exception as e:
                            logger.warning(f"下载人脸时出错: {str(e)}")
                    
                    return True, json_response
                else:
                    error_message = json_response.get("errorMessage") or json_response.get("message") or "未知错误"
                    logger.error(f"主播认证申请失败: {error_message}")
                    return False, json_response
            except json.JSONDecodeError as e:
                # 响应不是JSON格式
                logger.error(f"无法解析响应JSON: {str(e)}")
                logger.info(f"原始响应内容: {response.text}")
                if response.status_code == 200:
                    # 状态码正常但不是JSON，可能是其他响应格式
                    logger.warning("服务器返回状态码200但未返回JSON，可能是成功响应")
                    return True, {"message": "请求可能成功，但返回格式不是JSON"}
                else:
                    return False, {"error": str(e), "raw_response": response.text}
        except Exception as e:
            logger.error(f"请求过程中发生异常: {str(e)}")
            return False, {"error": str(e)}
    
    @staticmethod
    def save_base64_to_image(base64_str, file_path):
        """
        将base64编码的字符串保存为图片文件
        :param base64_str: base64编码的字符串
        :param file_path: 保存的文件路径
        :return: 是否成功
        """
        try:
            # 如果字符串包含前缀（如"data:image/png;base64,"），则移除
            if "," in base64_str:
                base64_str = base64_str.split(",", 1)[1]
            
            # 解码base64字符串
            image_data = base64.b64decode(base64_str)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 保存为文件
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"已成功保存base64编码的图片到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存base64编码的图片失败: {str(e)}")
            return False 