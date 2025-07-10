#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils.logger import logger


class AgencyBusinessAPI:
    """
    管理后台代理业务相关API封装
    """
    
    @staticmethod
    def check_agent_account(client, agent_ids, status=2):
        """
        审核代理账号
        :param client: 管理客户端
        :param agent_ids: 代理ID或代理ID列表
        :param status: 审核状态：2审核通过，默认2
        :return: (是否全部成功, 成功数量, 总数量, 响应对象列表)
        """
        url = "/admin/agent/account/check"
        
        logger.info(f"审核代理账号: 数量={len(agent_ids)}, 状态={status}")
        
        success_count = 0
        responses = []
        
        # 对每个代理ID单独发送请求
        for agent_id in agent_ids:
            # 构造请求数据
            data = {"agentId": agent_id, "status": status}
            
            # 使用PUT方法
            response = client.put(url, json=data)
            responses.append(response)
            
            # 检查响应状态码是否为204（成功）
            if response.status_code == 204:
                logger.info(f"审核代理账号成功: ID={agent_id}")
                success_count += 1
            else:
                logger.error(f"审核代理账号失败: ID={agent_id}, HTTP {response.status_code}")
                try:
                    error_data = response.json() if response.text else {}
                    logger.error(f"错误详情: {error_data}")
                except:
                    logger.error(f"错误响应内容: {response.text}")
        
        # 判断是否全部成功
        all_success = success_count == len(agent_ids)
        logger.info(f"审核代理账号完成: 总数={len(agent_ids)}, 成功={success_count}, 失败={len(agent_ids) - success_count}")
        
        return all_success, success_count, len(agent_ids), responses 

    @staticmethod
    def generate_invite_code(client, num=1):
        """
        生成邀请码
        :param client: 管理客户端
        :param num: 生成数量
        :return: (是否成功, 响应对象)
        """
        url = "/admin/agent/generator/invite/code"
        logger.info(f"生成邀请码: 数量={num}")
        
        # 客户端会自动添加请求头
        response = client.post(url, json={"num": num})
        
        # 检查响应
        if response.status_code in [200, 201]:  # 接受200和201状态码
            # 处理可能的空响应(201可能没有响应体)
            if not response.text:
                logger.info(f"生成邀请码成功: 状态码={response.status_code}")
                # 重新获取邀请码列表
                return AgencyBusinessAPI.get_invite_code_list(client)
            else:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"生成邀请码成功: 数量={len(data)}")
                        return True, data
                    else:
                        logger.error(f"生成邀请码失败: 响应格式不符合预期")
                except Exception as e:
                    logger.error(f"解析响应失败: {str(e)}")
        else:
            logger.error(f"生成邀请码请求失败: HTTP {response.status_code}")
            # 记录更详细的错误信息
            try:
                error_data = response.json()
                logger.error(f"错误详情: {error_data}")
            except:
                logger.error(f"错误响应内容: {response.text}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def get_invite_code_list(client, page=0, size=10, sort="id,desc"):
        """
        获取邀请码列表
        :param client: 管理客户端
        :param page: 页码
        :param size: 每页数量
        :param sort: 排序方式
        :return: (是否成功, 响应对象)
        """
        url = "/admin/agent/invite/code/list"
        logger.info(f"获取邀请码列表: 页码={page}, 每页数量={size}")
        
        params = {
            "page": page,
            "size": size,
            "sort": sort
        }
        
        # 客户端会自动添加请求头
        response = client.get(url, params=params)
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if "content" in data:
                logger.info(f"获取邀请码列表成功: 数量={len(data['content'])}")
                return True, data
            else:
                logger.error(f"获取邀请码列表失败: 响应格式不符合预期")
        else:
            logger.error(f"获取邀请码列表请求失败: HTTP {response.status_code}")
        
        return False, response.json() if response.text else {}

    @staticmethod
    def get_unused_invite_code(client):
        """
        获取未使用的邀请码
        :param client: 管理客户端
        :return: (是否成功, 邀请码, 响应对象)
        """
        # 获取邀请码列表
        success, data = AgencyBusinessAPI.get_invite_code_list(client)
        
        if success:
            # 查找未使用的邀请码(status=0)
            content = data.get("content", [])
            for item in content:
                if item.get("status") == 0:
                    invite_code = item.get("inviteCode")
                    logger.info(f"获取未使用的邀请码成功: {invite_code}")
                    return True, invite_code, data
            
            # 如果没有找到未使用的邀请码，则生成新的
            logger.info("未找到未使用的邀请码，正在生成新的邀请码")
            success, gen_data = AgencyBusinessAPI.generate_invite_code(client, 1)
            
            if success and gen_data:
                # 重新获取邀请码列表
                return AgencyBusinessAPI.get_unused_invite_code(client)
            else:
                logger.error("生成新邀请码失败")
                return False, None, data
        else:
            logger.error("获取邀请码列表失败")
            return False, None, data 