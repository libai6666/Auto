#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def main():
    """
    测试管理后台登录和生成邀请码
    """
    print("=" * 80)
    print(f"测试管理后台请求开始: {datetime.now()}")
    
    # 登录请求
    login_url = "https://api.duoo.work/admin/auth/login"
    login_data = {
        "username": "admin",
        "password": "W67hW7/uh9cav+hRF71uJFut0Cnrtf8T0KsaawUocDfuJAuDWr+zutnakwEybnn2WDlYAdyZiaJaNw8pH6pDzQ=="
    }
    login_headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Host": "api.duoo.work"
    }
    
    print("发送登录请求...")
    login_response = requests.post(login_url, json=login_data, headers=login_headers)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get("token")
        print(f"登录成功，获取token: {token[:30]}...")
        
        # 生成邀请码请求
        invite_url = "https://api.duoo.work/admin/agent/generator/invite/code"
        invite_data = {"num": 1}
        
        # 使用获取的token设置Authorization头
        invite_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Host": "api.duoo.work",
            "Authorization": token  # 直接使用token，不添加Bearer前缀
        }
        
        print("发送生成邀请码请求...")
        print(f"请求头: {invite_headers}")
        invite_response = requests.post(invite_url, json=invite_data, headers=invite_headers)
        
        print(f"响应状态码: {invite_response.status_code}")
        print(f"响应内容: {invite_response.text}")
        
        # 尝试添加Bearer前缀再次请求
        if invite_response.status_code != 200:
            print("\n尝试使用Bearer前缀...")
            invite_headers["Authorization"] = f"Bearer {token}" if not token.startswith("Bearer ") else token
            print(f"请求头: {invite_headers}")
            invite_response = requests.post(invite_url, json=invite_data, headers=invite_headers)
            
            print(f"响应状态码: {invite_response.status_code}")
            print(f"响应内容: {invite_response.text}")
    else:
        print(f"登录失败: {login_response.status_code}")
        print(f"响应内容: {login_response.text}")
    
    print("=" * 80)

if __name__ == "__main__":
    main() 