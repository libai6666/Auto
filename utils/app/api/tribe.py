#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
家族相关API接口
"""

from utils.logger import logger


class TribeAPI:
    """家族相关API接口封装"""

    @staticmethod
    def apply(client, tribe_id):
        """
        申请加入家族
        :param client: API客户端实例（已登录）
        :param tribe_id: 家族ID
        :return: (是否成功, 响应对象)
        """
        apply_data = {
            "tribeId": tribe_id,
            "apply": 1  # 1: 申请加入
        }

        try:
            response = client.request(
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

            uid = client.get_user_id() if hasattr(client, "get_user_id") else "?"
            logger.info(f"用户 {uid} 成功申请加入家族 {tribe_id}")
            return True, response

        except Exception as e:
            logger.error(f"申请家族异常: {str(e)}")
            return False, None

    @staticmethod
    def approve(client, uid, tribe_id, status=1):
        """
        家族长同意/拒绝成员申请
        :param client: 家族长客户端（已登录）
        :param uid: 申请用户ID
        :param tribe_id: 家族ID
        :param status: 1：审核通过、2：审核不通过、3：同意退会、4：拒绝退会、5：踢出家族
        :return: (是否成功, 响应对象)
        """
        approve_data = {
            "uid": uid,
            "tribeId": tribe_id,
            "status": status
        }

        try:
            response = client.request(
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
