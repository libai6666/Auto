#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.client_factory import ClientFactory
from utils.logger import logger
from utils.app.api.user import UserAPI
from utils.agent_backend.api.agent import AgentAPI
from utils.manage_backend.api.manager import ManagerAPI


def parse_args():
    """
    解析命令行参数
    :return: 解析结果
    """
    parser = argparse.ArgumentParser(description="主播绑定代理脚本")
    
    # 主播参数
    parser.add_argument("--anchor-phone", type=str, required=True, help="主播手机号")
    parser.add_argument("--anchor-area-code", type=str, default="43", help="主播国别码")
    
    # 代理参数
    parser.add_argument("--agent-phone", type=str, required=True, help="代理手机号")
    parser.add_argument("--agent-area-code", type=str, default="86", help="代理国别码")
    
    # 环境参数
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="test", help="执行环境")
    
    # 调试参数
    parser.add_argument("--debug", action="store_true", help="是否开启调试模式")
    
    return parser.parse_args()


def setup_environment(env):
    """
    设置环境变量
    :param env: 环境名称
    """
    os.environ["PYTEST_ENV"] = env
    logger.info(f"设置执行环境: {env}")


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 设置环境
    setup_environment(args.env)
    
    # 记录执行开始信息
    logger.info("=" * 80)
    logger.info(f"主播绑定代理开始，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"主播手机号: {args.anchor_area_code}-{args.anchor_phone}")
    logger.info(f"代理手机号: {args.agent_area_code}-{args.agent_phone}")
    logger.info(f"执行环境: {args.env}")
    logger.info("=" * 80)
    
    # 创建客户端工厂
    factory = ClientFactory()
    
    # 步骤1: 主播登录
    logger.info("步骤1: 主播登录")
    anchor_client = factory.create_custom_client(args.anchor_phone, args.anchor_area_code)
    if not UserAPI.login(anchor_client):
        logger.error("主播登录失败，无法继续执行")
        return
    
    # 检查用户是否是主播
    if not UserAPI.is_anchor(anchor_client):
        logger.error("当前用户不是主播，无法继续执行")
        return
    
    # 获取主播ID
    anchor_id = anchor_client.user_info.get("uid")
    logger.info(f"主播ID: {anchor_id}")
    
    # 步骤2: 创建代理客户端和管理员客户端
    logger.info("步骤2: 创建代理客户端和管理员客户端")
    agent_identifier = f"agent_{args.agent_area_code}_{args.agent_phone}"
    agent_client = factory.create_agent_client(agent_identifier)
    agent_client.phone = args.agent_phone
    agent_client.area_code = args.agent_area_code
    
    manager_client = factory.create_manager_client()
    
    # 登录管理后台
    success, _ = ManagerAPI.login(manager_client)
    if not success:
        logger.error("登录管理后台失败，无法继续执行")
        return
    
    # 步骤3: 发送验证码
    logger.info("步骤3: 发送验证码")
    success, _ = AgentAPI.send_code(agent_client, args.agent_area_code, args.agent_phone)
    if not success:
        logger.error(f"发送验证码失败，无法继续执行")
        return
    
    # 步骤4: 获取验证码
    logger.info("步骤4: 获取验证码")
    success, code, _ = AgentAPI.get_code(manager_client, args.agent_area_code, args.agent_phone)
    if not success or not code:
        logger.error(f"获取验证码失败，无法继续执行")
        return
    
    logger.info(f"获取验证码成功: {code}")
    
    # 步骤5: 代理登录
    logger.info("步骤5: 代理登录")
    success, agent_data = AgentAPI.login(
        agent_client,
        args.agent_area_code,
        args.agent_phone,
        code=code
    )
    
    if not success:
        logger.error("代理登录失败，无法继续执行")
        return
    
    agent_id = agent_client.agent_id
    logger.info(f"代理登录成功，代理ID: {agent_id}")
    
    # 步骤6: 主播申请绑定代理
    logger.info("步骤6: 主播申请绑定代理")
    success, response = UserAPI.apply_bind_agent(anchor_client, agent_id)
    if not success:
        logger.error("主播申请绑定代理失败，无法继续执行")
        return
    
    logger.info("主播申请绑定代理成功，等待代理审核")
    
    # 等待几秒，确保申请已经提交到系统
    time.sleep(3)
    
    # 步骤7: 代理获取绑定申请列表
    logger.info("步骤7: 代理获取绑定申请列表")
    success, records, response = AgentAPI.get_bind_list(
        agent_client,
        page_index=1,
        page_size=10,
        actor_id=anchor_id
    )
    
    if not success or not records:
        logger.error("获取绑定申请列表失败或列表为空，无法继续执行")
        return
    
    # 查找当前主播的绑定申请
    bind_record = None
    for record in records:
        if record.get("actorId") == anchor_id and record.get("status") == 2:  # 状态2表示审核中
            bind_record = record
            break
    
    if not bind_record:
        logger.error(f"未找到主播ID={anchor_id}的待审核绑定申请")
        return
    
    record_id = bind_record.get("id")
    logger.info(f"找到绑定申请记录: ID={record_id}, 主播昵称={bind_record.get('nickname')}")
    
    # 步骤8: 代理审核绑定申请
    logger.info("步骤8: 代理审核绑定申请")
    success, response = AgentAPI.check_bind(agent_client, record_id, 3)  # 状态3表示通过
    
    if not success:
        logger.error("审核绑定申请失败")
        return
    
    logger.info(f"审核绑定申请成功，主播ID={anchor_id}已成功绑定到代理ID={agent_id}")
    
    # 记录执行结果
    logger.info("=" * 80)
    logger.info(f"主播绑定代理完成，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"主播ID: {anchor_id}, 手机号: {args.anchor_area_code}-{args.anchor_phone}")
    logger.info(f"代理ID: {agent_id}, 手机号: {args.agent_area_code}-{args.agent_phone}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main() 