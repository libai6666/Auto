#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import re
import os
from utils.api_client import APIClient
from utils.logger import logger
from utils.data_handler import load_config
from utils.api.user import UserAPI
from pypinyin import lazy_pinyin


class UserClient(APIClient):
    """
    代表特定用户的API客户端
    """
    def __init__(self, user_config, base_url=None, timeout=None):
        """
        初始化用户客户端
        :param user_config: 用户配置字典，包含phoneNumber和phoneCode
        :param base_url: API基础URL
        :param timeout: 超时时间
        """
        super().__init__(base_url, timeout)
        
        self.user_config = user_config
        self.access_token = None
        self.user_info = None
        
        # 设置公共头
        common_headers = {
            "d": "111",
            "p": "1",
            "v": "5.8.1",
            "l": "zh-en",
            "appName": "duoo",
            "bizId": "1",
            "Content-Type": "application/json"
        }
        self.session.headers.update(common_headers)
    
    def login(self, force=False):
        """
        执行登录流程
        :param force: 是否强制重新登录
        :return: 登录是否成功
        """
        return UserAPI.login(self, force)
    
    def request(self, method, url, params=None, data=None, json=None, headers=None, files=None, auto_login=True, **kwargs):
        """
        重写请求方法，添加自动登录功能
        :param method: 请求方法
        :param url: 请求URL
        :param params: URL参数
        :param data: 请求数据
        :param json: JSON数据
        :param headers: 请求头
        :param files: 文件
        :param auto_login: 是否自动登录，默认为True
        :param kwargs: 其他参数
        :return: 响应对象
        """
        # 自动登录（如果需要且不是登录相关接口）
        if auto_login and not self.access_token and not url.endswith(("login/sendSms", "login", "operate/submit")):
            logger.info("需要登录后才能访问，正在自动登录...")
            if not self.login():
                raise Exception("自动登录失败，无法继续请求")
        
        # 发送请求
        return super().request(method, url, params, data, json, headers, files, **kwargs)
    
    def get_user_id(self):
        """获取用户ID"""
        return self.user_info["uid"] if self.user_info else None
    
    def get_user_nick(self):
        """获取用户昵称"""
        return self.user_info["nick"] if self.user_info else None
    
    def get_user_role(self):
        """获取用户角色"""
        return self.user_info["userRoles"][0] if self.user_info and "userRoles" in self.user_info else None
    
    def get_user_role_description(self):
        """
        获取用户身份描述
        根据userRoles数组判断用户身份
        :return: 用户身份描述
        """
        return UserAPI.get_user_role_description(self)
    
    def modify_nick(self, new_nick):
        """
        修改用户昵称
        :param new_nick: 新昵称
        :return: (是否成功, 响应对象)
        """
        return UserAPI.modify_nick(self, new_nick)
    
    def modify_profile(self, gender=None, birthday=None, country=None):
        """
        完善用户资料
        :param gender: 性别 1：男 2：女
        :param birthday: 生日，格式: YYYY-MM-DD
        :param country: 国家
        :return: (是否成功, 响应对象)
        """
        return UserAPI.modify_profile(self, gender, birthday, country)
    
    def apply_for_anchor(self, photo_path=None):
        """
        申请主播认证
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
        uid = self.get_user_id()
        if not uid:
            logger.error("无法获取用户ID，申请主播失败")
            return False, None
            
        # 提取用户ID后三位并转换为拼音
        uid_last_three = str(uid)[-3:]
        pinyin_list = []
        for digit in uid_last_three:
            # 将数字转为汉字，再转为拼音
            chinese_digit = self._number_to_chinese(int(digit))
            pinyin = ''.join(lazy_pinyin(chinese_digit))
            pinyin_list.append(pinyin)
        
        # 构造昵称: A + UID后三位拼音
        nick = "A" + ''.join(pinyin_list)
        
        # 获取照片数据
        logger.info(f"使用指定图片文件作为头像和人脸照片: {photo_path}")
        photo_data = UserAPI.load_photo_from_file(photo_path)
        if photo_data is None:
            logger.error(f"加载照片文件失败: {photo_path}")
            return False, None
        
        logger.info(f"成功加载指定图片文件: {photo_path}，图片大小: {len(photo_data)/1024:.2f} KB")
        
        # 申请主播认证
        success, response = UserAPI.apply_for_anchor_certification(self, nick, photo_data, photo_data)
        
        # 如果成功，记录详细信息并验证图片URL
        if success:
            logger.info(f"用户 {self.get_user_nick()} (ID: {self.get_user_id()}) 成功申请主播认证")
            
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
            if "avatar" in data and self.user_info:
                self.user_info["avatar"] = data["avatar"]
                logger.info("已更新用户信息中的头像URL")
        
        return success, response
    
    def _number_to_chinese(self, number):
        """将数字转换为汉字"""
        chinese_dict = {
            0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
            5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
        }
        return chinese_dict.get(number, '零')

if __name__ == "__main__":
    user_config = {
        "phoneNumber": "17441",
        "phoneCode": "43"
    }
    user_client = UserClient(user_config)
    user_client.login()
