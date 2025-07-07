#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.client_factory import ClientFactory
from utils.logger import logger
from utils.manage_backend.api.admin import AdminAPI
from utils.agent_backend.api.agent import AgentAPI


def parse_args():
    """
    解析命令行参数
    :return: 解析结果
    """
    parser = argparse.ArgumentParser(description="批量注册代理脚本")
    
    # 基本参数
    parser.add_argument("--count", "-c", type=int, default=1, help="要注册的代理数量")
    parser.add_argument("--base-phone", type=str, default="18211761190", help="基础手机号，会依次递增")
    parser.add_argument("--area-code", type=str, default="86", help="国别码")
    
    # 代理信息参数
    parser.add_argument("--name-prefix", type=str, default="autoAgent", help="代理名称前缀，会加上手机号后四位")
    parser.add_argument("--country", type=str, choices=["CN", "IN"], default=None, help="国家代码，如果不指定则随机选择")
    
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


def get_random_country():
    """
    随机获取国家代码
    :return: 国家代码
    """
    countries = ["CN", "IN"]
    return random.choice(countries)


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
    logger.info(f"批量注册代理开始，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"要注册的代理数量: {args.count}")
    logger.info(f"基础手机号: {args.base_phone}")
    logger.info(f"国别码: {args.area_code}")
    logger.info(f"代理名称前缀: {args.name_prefix}")
    logger.info(f"国家: {args.country if args.country else '随机'}")
    logger.info(f"执行环境: {args.env}")
    logger.info("=" * 80)
    
    # 创建客户端工厂
    factory = ClientFactory()
    
    # 创建管理后台客户端
    admin_client = factory.create_admin_client()
    
    # 登录管理后台
    success, _ = AdminAPI.login(admin_client)
    if not success:
        logger.error("登录管理后台失败，无法继续执行")
        return
    
    # 生成邀请码
    success, _ = AdminAPI.generate_invite_code(admin_client, args.count)
    if not success:
        logger.warning("生成邀请码失败，将尝试使用现有邀请码")
    
    # 批量创建代理客户端
    agent_clients = factory.create_agent_clients(args.count, args.base_phone, args.area_code)
    
    # 注册结果统计
    success_count = 0
    failed_count = 0
    
    # 开始批量注册
    for i, agent_client in enumerate(agent_clients):
        # 获取代理信息
        phone = agent_client.phone
        area_code = agent_client.area_code
        
        # 生成代理名称
        agent_name = f"{args.name_prefix}{phone[-4:]}"
        
        # 确定国家
        country = args.country if args.country else get_random_country()
        
        logger.info(f"正在注册第 {i+1}/{args.count} 个代理: {area_code}-{phone}")
        
        try:
            # 发送验证码
            success, _ = AgentAPI.send_code(agent_client, area_code, phone)
            if not success:
                logger.error(f"发送验证码失败，跳过注册: {area_code}-{phone}")
                failed_count += 1
                continue
            
            # 获取验证码
            success, code, _ = AgentAPI.get_code(admin_client, area_code, phone)
            if not success or not code:
                logger.error(f"获取验证码失败，跳过注册: {area_code}-{phone}")
                failed_count += 1
                continue
            
            # 获取未使用的邀请码
            success, invite_code, _ = AdminAPI.get_unused_invite_code(admin_client)
            if not success or not invite_code:
                logger.error(f"获取邀请码失败，跳过注册: {area_code}-{phone}")
                failed_count += 1
                continue
            
            # 注册代理
            success, response = AgentAPI.register_agent(
                agent_client, 
                area_code, 
                phone, 
                code, 
                invite_code, 
                agent_name, 
                country,
                login_type="1"  # 使用短信验证码登录
            )
            
            if success:
                # 记录成功信息
                agent_id = response.get("agentId")
                token = response.get("token")
                logger.info(f"注册代理成功: ID={agent_id}, 手机号={area_code}-{phone}, 名称={agent_name}")
                success_count += 1
                
                # 输出代理Token，方便后续使用
                logger.debug(f"代理Token: {token}")
                
                # 防止请求过于频繁，稍作延迟
                time.sleep(1)
            else:
                logger.error(f"注册代理失败: {area_code}-{phone}")
                failed_count += 1
        
        except Exception as e:
            logger.error(f"注册代理异常: {str(e)}")
            failed_count += 1
    
    # 记录执行结果
    logger.info("=" * 80)
    logger.info(f"批量注册代理完成，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"成功注册: {success_count} 个")
    logger.info(f"失败注册: {failed_count} 个")
    logger.info("=" * 80)


if __name__ == "__main__":
    main() 