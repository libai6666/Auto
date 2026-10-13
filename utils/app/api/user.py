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
    def login(client, force=False, login_type="phone", max_retries=3, retry_delay=5):
        """
        执行登录流程
        :param client: API客户端实例
        :param force: 是否强制重新登录
        :param login_type: 登录类型，支持 "phone"(手机验证码)、"google"(Google登录)、"account"(账号密码)
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟（秒）
        :return: 登录是否成功
        """
        # 如果已经有access_token且不强制登录，则直接返回成功
        if client.access_token and not force:
            return True
        
        # 验证登录类型
        if login_type not in ["phone", "google", "account"]:
            logger.error(f"不支持的登录类型: {login_type}，支持的类型有: phone, google, account")
            return False
        
        # 检查必要的配置参数
        if login_type == "phone" and (not client.user_config.get("phoneNumber") or not client.user_config.get("phoneCode")):
            logger.error("手机登录缺少必要参数: phoneNumber 或 phoneCode")
            return False
        elif login_type == "google" and not client.user_config.get("google_token"):
            logger.error("Google登录缺少必要参数: google_token")
            return False
        elif login_type == "account" and (not client.user_config.get("account") or not client.user_config.get("password")):
            logger.error("账号密码登录缺少必要参数: account 或 password")
            return False
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 根据登录类型从user_config中获取参数
                if login_type == "phone":
                    return UserAPI.login_direct(
                        client,
                        channel="phone",
                        token=client.user_config["phoneNumber"],
                        phoneCode=client.user_config["phoneCode"],
                        deviceType=client.user_config.get("deviceType", "android")
                    )
                elif login_type == "google":
                    return UserAPI.login_direct(
                        client,
                        channel="google",
                        token=client.user_config["google_token"],
                        password=client.user_config.get("password"),
                        deviceType=client.user_config.get("deviceType", "android")
                    )
                elif login_type == "account":
                    return UserAPI.login_direct(
                        client,
                        channel="account",
                        token=client.user_config["account"],
                        password=client.user_config["password"],
                        deviceType=client.user_config.get("deviceType", "android")
                    )
            except Exception as e:
                logger.error(f"登录过程中发生错误: {str(e)}")
                retry_count += 1
                time.sleep(retry_delay)
        
        logger.error(f"登录失败，已达到最大重试次数 {max_retries}")
        return False

    @staticmethod
    def mock_refresh(client, uid, country="IN", role_level=3):
        """
        通过mockRefresh接口获取指定uid的真实token（不修改client状态）
        :param client: API客户端实例
        :param uid: 用户ID
        :param country: 国家码，默认IN
        :param role_level: 角色等级：1 用户、3 主播、5 代理，默认3
        :return: (是否成功, access_token, user_info)
        """
        try:
            response = client.request(
                method="POST",
                url="/api/user/v1/user/mockRefresh",
                json={"uid": uid, "country": country, "roleLevel": role_level}
            )

            if response.status_code != 200:
                logger.error(f"mockRefresh失败: HTTP {response.status_code}: {response.text[:200]}")
                return False, None, None

            result = response.json()
            if result.get("errorCode") != 0:
                logger.error(f"mockRefresh失败: {result.get('errorMessage')}")
                return False, None, None

            data = result.get("data") or {}
            access_token = data.get("accessToken") or data.get("token")
            user_info = data.get("userInfo") or {"uid": uid}

            if not access_token:
                logger.error(f"mockRefresh失败: 响应中未返回accessToken, data={data}")
                return False, None, None

            return True, access_token, user_info

        except Exception as e:
            logger.error(f"mockRefresh异常: {str(e)}")
            return False, None, None

    @staticmethod
    def _handle_login_response(client, login_response):
        """
        处理登录响应
        :param client: API客户端实例
        :param login_response: 登录响应
        :return: 登录是否成功
        """
        # 检查登录是否成功
        if login_response.status_code != 200:
            logger.error(f"登录失败: {login_response.text}")
            return False
        
        login_result = login_response.json()
        if login_result.get("errorCode") != 0:
            logger.error(f"登录失败: {login_result.get('errorMessage')}")
            return False
        
        # 保存token和用户信息
        client.access_token = login_result["data"]["accessToken"]
        client.user_info = login_result["data"]["userInfo"]
        
        # 更新Authorization头
        client.session.headers.update({"Authorization": client.access_token})
        
        # 获取用户身份描述
        role_description = UserAPI.get_user_role_description(client)
        
        logger.info(f"登录成功，用户ID: {client.user_info['uid']}, 昵称: {client.user_info['nick']}, 身份: {role_description}")
        return True
    
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
    def modify_profile(client, gender=None, birthday=None, country=None, lang=None, videoUrl=None):
        """
        完善用户资料
        :param client: API客户端实例
        :param gender: 性别 1：男 2：女
        :param birthday: 生日，格式: YYYY-MM-DD
        :param country: 国家
        :param lang: 语言
        :param videoUrl: 白名单主播视频地址
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
        if lang is not None:
            data["lang"] = lang
        if videoUrl is not None:
            data["videoUrl"] = videoUrl
        
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
    def get_local_photo_required(client=None):
        """
        获取是否需要本地图片
        :param client: API客户端实例（可选）
        :return: 是否需要本地图片
        """
        # 根据环境或配置决定是否需要使用本地图片
        # 这里简单返回True
        return True
    
    @staticmethod
    def load_photo_from_file(client=None, file_path=None):
        """
        从文件加载照片数据
        :param client: API客户端实例（可选）
        :param file_path: 照片文件路径
        :return: Base64编码的照片数据
        """
        # 兼容旧的调用方式
        if client is not None and file_path is None:
            file_path = client
            client = None
            
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
    def save_base64_to_image(client=None, base64_str=None, file_path=None):
        """
        保存Base64编码的图片到文件
        :param client: API客户端实例（可选）
        :param base64_str: Base64编码的图片数据
        :param file_path: 保存路径
        :return: 是否成功
        """
        # 兼容旧的调用方式
        if client is not None and base64_str is not None and file_path is None:
            file_path = base64_str
            base64_str = client
            client = None
            
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
        判断用户是否为主播
        :param client: API客户端实例
        :return: 是否为主播
        """
        if not client.user_info or "userRoles" not in client.user_info:
            return False
        
        # 检查userRoles数组是否包含主播角色
        user_roles = client.user_info["userRoles"]
        return 3 in user_roles  # 3表示主播角色
        
    @staticmethod
    def modify_avatar(client, avatar):
        """
        修改用户头像
        :param client: API客户端实例
        :param avatar: 头像地址
        :return: (是否成功, 响应对象)
        """
        response = client.request(
            method="POST",
            url="/api/user/v1/user/modifyAvatar",
            json={"avatar": avatar}
        )
        
        if response.status_code != 200:
            logger.error(f"修改头像失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"修改头像失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if client.user_info:
            client.user_info["avatar"] = avatar
        
        logger.info(f"修改头像成功: {avatar}")
        return True, response
    
    @staticmethod
    def get_user_info(client, uid=None):
        """
        获取用户资料
        :param client: API客户端实例
        :param uid: 用户ID，不传则获取自己的资料
        :return: (是否成功, 响应对象)
        """
        # 构建请求参数
        params = {}
        if uid is not None:
            params["uid"] = uid
            params["targetId"] = uid  # 同时设置targetId为相同的uid
        else:
            # 如果没有指定uid，则使用当前登录用户的uid
            if client.user_info and "uid" in client.user_info:
                params["uid"] = client.user_info["uid"]
                params["targetId"] = client.user_info["uid"]  # 同时设置targetId
            else:
                logger.error("获取用户资料失败: 未指定用户ID且未登录")
                return False, None

        response = client.request(
            method="GET",
            url="/api/user/v1/user/info",
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"获取用户资料失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"获取用户资料失败: {result.get('errorMessage')}")
            return False, response
        
        # 更新本地用户信息
        if result.get("data"):
            # 只有当查询的是自己的信息时，才更新本地用户信息
            if str(params.get("uid")) == str(client.user_info.get("uid", "")):
                client.user_info = result.get("data")
            logger.info(f"成功获取用户资料: {result['data'].get('nick')} (ID: {result['data'].get('uid')})")
        
        return True, response
        
    @staticmethod
    def get_online_pay_users(client):
        """
        获取在线付费用户列表
        :param client: API客户端实例
        :return: (是否成功, 响应对象)
        """
        response = client.request(
            method="GET",
            url="/api/user/v1/user/online/pay"
        )
        
        if response.status_code != 200:
            logger.error(f"获取在线付费用户列表失败: {response.text}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"获取在线付费用户列表失败: {result.get('errorMessage')}")
            return False, response
        
        # 获取用户列表，如果为None则使用空列表
        users = result.get("data", {}).get("list") or []
        logger.info(f"成功获取在线付费用户列表，共 {len(users)} 个用户")
        
        return True, response 

    @staticmethod
    def apply_for_anchor(client, photo_path=None):
        """
        申请主播认证
        :param client: API客户端实例
        :param photo_path: 必须，指定照片文件路径，用作头像和人脸照片
        :return: (是否成功, 响应对象)
        """
        # 检查必须提供照片路径
        if not photo_path:
            logger.error("必须提供照片路径！申请主播认证需要头像和人脸照片")
            return False, None
            
        # 检查文件是否存在
        # 如果是相对路径，尝试从当前目录开始解析
        if not os.path.isabs(photo_path) and not os.path.exists(photo_path):
            # 尝试从当前目录解析
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abs_photo_path = os.path.join(current_dir, photo_path)
            if os.path.exists(abs_photo_path):
                logger.info(f"使用绝对路径: {abs_photo_path}")
                photo_path = abs_photo_path
            else:
                # 再尝试从工作目录解析
                work_dir_path = os.path.join(os.getcwd(), photo_path)
                if os.path.exists(work_dir_path):
                    logger.info(f"使用工作目录路径: {work_dir_path}")
                    photo_path = work_dir_path
        
        # 最终检查文件是否存在
        if not os.path.exists(photo_path):
            logger.error(f"指定的照片文件不存在: {photo_path}")
            logger.error("请确保路径正确，可以使用绝对路径或相对于工作目录的路径")
            return False, None
            
        # 获取用户ID的后三位
        uid = client.get_user_id()
        if not uid:
            logger.error("无法获取用户ID，申请主播失败")
            return False, None
            
        # 提取用户ID后三位并转换为拼音
        uid_last_three = str(uid)[-3:]
        
        # 导入pypinyin，仅在此函数中使用
        try:
            from pypinyin import lazy_pinyin
            
            # 将数字转为汉字，再转为拼音的函数
            def number_to_chinese(number):
                chinese_dict = {
                    0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
                    5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
                }
                return chinese_dict.get(number, '零')
                
            pinyin_list = []
            for digit in uid_last_three:
                # 将数字转为汉字，再转为拼音
                chinese_digit = number_to_chinese(int(digit))
                pinyin = ''.join(lazy_pinyin(chinese_digit))
                pinyin_list.append(pinyin)
            
            # 构造昵称: A + UID后三位拼音
            nick = "A" + ''.join(pinyin_list)
            
        except ImportError:
            # 如果没有安装pypinyin，使用简单的昵称
            logger.warning("未安装pypinyin模块，使用简单昵称")
            nick = "A" + uid_last_three
        
        # 获取照片数据
        logger.info(f"使用指定图片文件作为头像和人脸照片: {photo_path}")
        photo_data = UserAPI.load_photo_from_file(client, photo_path)
        if photo_data is None:
            logger.error(f"加载照片文件失败: {photo_path}")
            return False, None
        
        logger.info(f"成功加载指定图片文件: {photo_path}，图片大小: {len(photo_data)/1024:.2f} KB")
        
        # 申请主播认证
        success, response = UserAPI.apply_for_anchor_certification(client, nick, photo_data, photo_data)
        
        # 如果成功，记录详细信息并验证图片URL
        if success:
            logger.info(f"用户 {client.get_user_nick()} (ID: {client.get_user_id()}) 成功申请主播认证")
            
            # 进一步验证URL是否有效
            data = response.get("data", {})
            avatar_url = data.get("avatar")
            face_url = data.get("face")
            
            if avatar_url:
                logger.info(f"头像URL: {avatar_url}")
                try:
                    # 解析URL格式
                    url_parts = avatar_url.split("/")
                    if len(url_parts) >= 7:
                        year = url_parts[-4]
                        month = url_parts[-3]
                        day = url_parts[-2]
                        file_name = url_parts[-1]
                        logger.info(f"URL解析: 年份={year}, 月份={month}, 日期={day}, 文件名={file_name}")
                except Exception as e:
                    logger.warning(f"解析头像URL时出错: {str(e)}")
            
            # 更新用户信息中的头像URL
            if "avatar" in data and client.user_info:
                client.user_info["avatar"] = data["avatar"]
                logger.info("已更新用户信息中的头像URL")
        
        return success, response 

    @staticmethod
    def login_direct(client, channel="phone", token=None, password=None, phoneCode=None, smsCode=None, 
                    deviceId=None, inviteCode=None, anchorId=None, deviceType="android", bizId=1):
        """
        直接使用传入的参数执行登录流程
        :param client: API客户端实例
        :param channel: 登录渠道，支持 "phone"(手机验证码)、"google"(Google登录)、"account"(账号密码)、"apple"(Apple登录)
        :param token: 登录令牌，根据渠道不同而不同：
                     - phone: 手机号
                     - google: Google令牌
                     - account: 账号名
                     - apple: Apple令牌
        :param password: 密码（账号登录和Google登录时使用）
        :param phoneCode: 手机区号（手机登录时使用）
        :param smsCode: 短信验证码（手机登录时使用）
        :param deviceId: 设备号
        :param inviteCode: 注册邀请码
        :param anchorId: 链接地址中的主播id
        :param deviceType: 登录设备类型，如ios、android
        :param bizId: 包类型，默认为1
        :return: 登录是否成功
        """
        # 验证登录渠道
        if channel not in ["phone", "google", "account", "apple"]:
            logger.error(f"不支持的登录渠道: {channel}，支持的渠道有: phone, google, account, apple")
            return False
        
        # 检查必要的参数
        if not token:
            logger.error(f"登录失败: token参数是必须的")
            return False
        
        if channel == "phone" and not phoneCode:
            logger.error("手机登录缺少必要参数: phoneCode")
            return False
        
        if (channel == "account" or channel == "google") and not password:
            logger.error(f"{channel}登录缺少必要参数: password")
            return False
        
        # 如果是手机登录且未提供验证码，则自动获取
        if channel == "phone" and not smsCode:
            smsCode = UserAPI._get_phone_verification_code(client, token, phoneCode)
            if not smsCode:
                return False
        
        # 构建登录请求数据
        login_data = {
            "bizId": bizId,
            "channel": channel,
            "token": token,
            "deviceType": deviceType
        }
        
        # 根据不同登录渠道添加特定参数
        if channel == "phone":
            login_data["phoneCode"] = phoneCode
            login_data["smsCode"] = smsCode
        elif channel in ["account", "google"]:
            login_data["password"] = password
        
        # 添加可选参数（如果提供）
        if deviceId:
            login_data["deviceId"] = deviceId
        if inviteCode:
            login_data["inviteCode"] = inviteCode
        if anchorId:
            login_data["anchorId"] = anchorId
        
        try:
            # 执行登录请求
            login_response = client.request(
                method="POST",
                url="/api/user/v1/user/login",
                json=login_data,
                auto_login=False  # 防止递归调用
            )
            
            # 处理登录响应
            return UserAPI._handle_login_response(client, login_response)
            
        except Exception as e:
            logger.error(f"{channel}登录过程中发生错误: {str(e)}")
            return False
    
    @staticmethod
    def _get_phone_verification_code(client, phone_number, phone_code):
        """
        获取手机验证码
        :param client: API客户端实例
        :param phone_number: 手机号
        :param phone_code: 手机区号
        :return: 验证码，如果失败则返回None
        """
        import re
        
        try:
            # 发送短信验证码
            send_sms_response = client.request(
                method="POST",
                url="/api/user/v1/user/login/sendSms",
                json={
                    "phoneNum": phone_number,
                    "phoneCode": phone_code
                },
                auto_login=False  # 防止递归调用
            )
            
            # 检查发送短信是否成功
            if send_sms_response.status_code != 200:
                logger.error(f"发送短信验证码失败: {send_sms_response.text}")
                return None
            
            sms_result = send_sms_response.json()
            if sms_result.get("errorCode") != 0:
                error_message = sms_result.get('errorMessage', '')
                logger.error(f"发送短信验证码失败: {error_message}")
                return None
            
            logger.info(f"发送短信验证码成功，手机: {phone_code}-{phone_number}")
            
            # 获取实际验证码
            get_code_response = client.request(
                method="POST",
                url="/api/user/v1/operate/submit",
                json={
                    "operateName": "admin",
                    "phone": phone_number,
                    "areaCode": phone_code,
                    "operate": "App短信验证码"
                },
                auto_login=False  # 防止递归调用
            )
            
            # 检查获取验证码是否成功
            if get_code_response.status_code != 200:
                logger.error(f"获取验证码失败: {get_code_response.text}")
                return None
            
            code_result = get_code_response.json()
            if code_result.get("errorCode") != 0 or not code_result.get("succeed"):
                logger.error(f"获取验证码失败: {code_result.get('errorMessage')}")
                return None
            
            # 从响应中提取验证码
            code_message = code_result["data"]["jsonValue"]
            sms_code_match = re.search(r'验证码为 \[(\d+)\]', code_message)
            if not sms_code_match:
                logger.error(f"无法从响应中提取验证码: {code_message}")
                return None
            
            sms_code = sms_code_match.group(1)
            logger.info(f"成功获取验证码: {sms_code}")
            return sms_code
            
        except Exception as e:
            logger.error(f"获取手机验证码过程中发生错误: {str(e)}")
            return None 