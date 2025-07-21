#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
在线状态相关API接口
"""

from utils.logger import logger


class OnlineAPI:
    """在线状态相关API接口封装"""
    
    @staticmethod
    def report_heartbeat(client, status=1, roomId=None):
        """
        提交用户心跳
        :param client: API客户端实例
        :param status: 状态，默认为1（在线）
        :param roomId: 房间号，客户端在线心跳不需要发，这是服务端接口使用的参数
        :return: (是否成功, 响应对象)
        """
        # 构建请求数据
        data = {"status": status}
        if roomId is not None:
            data["roomId"] = roomId
        
        # 发送请求
        response = client.request(
            method="POST",
            url="/api/online/v1/online/report",
            json=data
        )
        
        # 检查响应
        if response.status_code != 200:
            logger.error(f"提交心跳失败: HTTP {response.status_code}")
            return False, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"提交心跳失败: {result.get('errorMessage')}")
            return False, response
        
        logger.debug(f"成功提交心跳，状态: {status}")
        return True, response
    
    @staticmethod
    def check_status(client, uids):
        """
        查询用户心跳状态
        :param client: API客户端实例
        :param uids: 用户ID列表
        :return: (是否成功, 状态字典, 响应对象)
        """
        # 确保uids是列表
        if not isinstance(uids, list):
            uids = [uids]
        
        # 发送请求
        response = client.request(
            method="POST",
            url="/api/online/v1/online/status",
            json={"uids": uids}
        )
        
        # 检查响应
        if response.status_code != 200:
            logger.error(f"查询心跳状态失败: HTTP {response.status_code}")
            return False, {}, response
        
        result = response.json()
        if result.get("errorCode") != 0:
            logger.error(f"查询心跳状态失败: {result.get('errorMessage')}")
            return False, {}, response
        
        # 获取状态字典
        status_map = result.get("data", {}).get("statusMap", {})
        logger.debug(f"成功查询心跳状态: {status_map}")
        
        return True, status_map, response
    
    @staticmethod
    def is_online(client, uid):
        """
        检查用户是否在线
        :param client: API客户端实例
        :param uid: 用户ID
        :return: 是否在线，如果查询失败则返回False
        """
        # 查询状态
        success, status_map, _ = OnlineAPI.check_status(client, [uid])
        if not success:
            return False
        
        # 检查状态是否为1（在线）
        return status_map.get(str(uid)) == 1 