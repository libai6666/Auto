#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
批量申请家族脚本
功能：
    访客模式：批量创建访客用户，申请加入指定家族，家族长自动同意申请
    指定uid模式：指定uid列表的用户通过mockRefresh登录，申请加入家族，家族长自动同意申请
家族长通过 mockRefresh 接口直接登录（家族ID与家族长uid一致）
示例：
    # 测试环境：10个访客申请加入家族 10035
    python scripts/batch_apply_tribe.py -c 10 -t 10035
    # 指定uid申请加入家族
    python scripts/batch_apply_tribe.py -t 10035 --uids 10001,10002,10003
    # 正式环境：指定uid申请加入家族 9011365
    python scripts/batch_apply_tribe.py --env prod -t 9011365 --uids 8387289,4000001
"""

import argparse
import time
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_handler import load_config
from utils.logger import logger
from utils.app.client.guest_client import GuestClient
from utils.app.client.mock_user_client import MockUserClient
from utils.app.api.tribe import TribeAPI


def login_leader(tribe_id, base_url, country, role_level):
    """登录家族长账号（家族ID即家族长uid）"""
    logger.info(f"正在登录家族长账号: uid={tribe_id}")
    leader_client = MockUserClient(base_url=base_url)
    if not leader_client.mock_login(tribe_id, country=country, role_level=role_level):
        logger.error("家族长登录失败，无法继续")
        return None
    logger.info(f"家族长登录成功，用户ID: {leader_client.get_user_id()}")
    return leader_client


def batch_apply_tribe(count, tribe_id, base_url, country, leader_role_level):
    """
    批量访客申请家族
    :param count: 访客数量
    :param tribe_id: 家族ID（与家族长uid一致）
    :return: 成功申请的用户列表
    """
    leader_client = login_leader(tribe_id, base_url, country, leader_role_level)
    if not leader_client:
        return []

    successful_guests = []

    for i in range(count):
        logger.info(f"\n========== 处理第 {i+1}/{count} 个访客 ==========")

        # 第一步：访客登录
        guest = GuestClient(base_url=base_url)
        if not guest.guest_login():
            logger.error(f"第 {i+1} 个访客登录失败，跳过")
            time.sleep(1)
            continue

        guest_uid = guest.get_user_id()

        # 第二步：申请加入家族
        time.sleep(1)  # 避免请求过于频繁
        success, _ = TribeAPI.apply(guest, tribe_id)
        if not success:
            logger.error(f"第 {i+1} 个访客申请家族失败，跳过")
            time.sleep(1)
            continue

        # 第三步：家族长同意申请
        time.sleep(1)
        success, _ = TribeAPI.approve(leader_client, guest_uid, tribe_id, status=1)
        if not success:
            logger.error(f"家族长同意第 {i+1} 个访客申请失败")
            time.sleep(1)
            continue

        successful_guests.append({
            "index": i + 1,
            "uid": guest_uid
        })

        logger.info(f"第 {i+1} 个访客成功加入家族！")
        time.sleep(2)  # 每个完整流程后延迟

    logger.info(f"\n========== 批量操作完成 ==========")
    logger.info(f"成功处理 {len(successful_guests)}/{count} 个访客")

    if successful_guests:
        logger.info("成功加入家族的用户列表:")
        for guest in successful_guests:
            logger.info(f"  - 第{guest['index']}个访客, UID: {guest['uid']}")

    return successful_guests


def batch_apply_uids(uids, tribe_id, base_url, country, role_level, leader_role_level):
    """
    指定uid列表的用户通过mockRefresh登录后申请加入家族
    :param uids: 申请用户uid列表
    :param tribe_id: 家族ID（与家族长uid一致）
    :return: 成功加入的uid列表
    """
    leader_client = login_leader(tribe_id, base_url, country, leader_role_level)
    if not leader_client:
        return []

    successful_uids = []

    for i, uid in enumerate(uids):
        logger.info(f"\n========== 处理第 {i+1}/{len(uids)} 个用户: uid={uid} ==========")

        # 第一步：mockRefresh登录
        client = MockUserClient(base_url=base_url)
        if not client.mock_login(uid, country=country, role_level=role_level):
            logger.error(f"用户 {uid} mockRefresh登录失败，跳过")
            time.sleep(1)
            continue

        # 第二步：申请加入家族
        time.sleep(1)  # 避免请求过于频繁
        success, _ = TribeAPI.apply(client, tribe_id)
        if not success:
            logger.error(f"用户 {uid} 申请家族失败，跳过")
            time.sleep(1)
            continue

        # 第三步：家族长同意申请
        time.sleep(1)
        success, _ = TribeAPI.approve(leader_client, uid, tribe_id, status=1)
        if not success:
            logger.error(f"家族长同意用户 {uid} 申请失败")
            time.sleep(1)
            continue

        successful_uids.append(uid)
        logger.info(f"用户 {uid} 成功加入家族！")
        time.sleep(2)  # 每个完整流程后延迟

    logger.info(f"\n========== 批量操作完成 ==========")
    logger.info(f"成功处理 {len(successful_uids)}/{len(uids)} 个用户")

    if successful_uids:
        logger.info(f"成功加入家族的用户: {','.join(str(uid) for uid in successful_uids)}")

    return successful_uids


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="批量申请家族工具")
    parser.add_argument("-c", "--count", type=int, default=None, help="访客数量（与--uids二选一）")
    parser.add_argument("-t", "--tribe-id", type=int, required=True, help="家族ID（与家族长uid一致）")
    parser.add_argument("--uids", help="指定申请用户uid，多个用逗号分隔；指定后忽略--count")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="test", help="执行环境，默认test")
    parser.add_argument("--country", default="IN", help="mockRefresh的country，默认IN")
    parser.add_argument("--role-level", type=int, default=1, help="申请用户mockRefresh的roleLevel：1用户、3主播、5代理，默认1")
    parser.add_argument("--leader-role-level", type=int, default=3, help="家族长mockRefresh的roleLevel，默认3（主播）")

    args = parser.parse_args()

    if args.tribe_id <= 0:
        parser.error("家族ID必须大于0")

    if not args.uids and not args.count:
        parser.error("必须指定 --count（访客数量）或 --uids（指定用户uid）")

    # 解析环境对应的base_url
    config = load_config()
    env = args.env or config.get("current_env", "test")
    base_url = (config.get("env_config", {}).get(env) or {}).get("base_url")
    if not base_url:
        parser.error(f"环境 {env} 未配置 base_url")
    logger.info(f"执行环境: {env} ({base_url})")

    if args.uids:
        uids = [int(item.strip()) for item in args.uids.split(",") if item.strip()]
        if not uids:
            parser.error("--uids 解析后为空")
        batch_apply_uids(uids, args.tribe_id, base_url, args.country, args.role_level, args.leader_role_level)
    else:
        if args.count <= 0:
            parser.error("访客数量必须大于0")
        batch_apply_tribe(args.count, args.tribe_id, base_url, args.country, args.leader_role_level)


if __name__ == "__main__":
    main()
