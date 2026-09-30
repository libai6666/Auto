#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
批量关注/取消关注脚本
功能：
    关注：从 token 区间（默认 10001-10600）随机抽取 N 个用户，并发关注目标用户
    取消关注：先查询目标用户的粉丝列表，取前 N 个粉丝（不足 N 个则全部），并发取消关注目标用户
示例：
    # 让 10035 被 50 个随机用户关注
    python scripts/batch_follow.py -t 10035 -c 50
    # 取消 10035 的 10 个粉丝（不足 10 个则全部取消）
    python scripts/batch_follow.py -t 10035 -c 10 --unfollow
    # 指定用户列表取消关注
    python scripts/batch_follow.py -t 10035 --uids 10001,10002,10003 --unfollow
"""

import argparse
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib3

from utils.api_client import APIClient
from utils.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOLLOW_URL = "/api/user/v1/relation/follow/modify"
FOLLOWERS_URL = "/api/user/v1/relation/followers"
FOLLOWERS_PAGE_SIZE = 50
DEFAULT_BIZ_ID = "7"
DEFAULT_D = "123456"

_thread_local = threading.local()


def get_client():
    client = getattr(_thread_local, "client", None)
    if client is None:
        client = APIClient()
        _thread_local.client = client
    return client


def build_headers(uid, biz_id, device):
    return {
        "token": str(uid),
        "BizId": str(biz_id),
        "d": str(device),
    }


def fetch_followers(target_uid, limit, biz_id, device):
    """查询目标用户的粉丝uid列表，最多返回 limit 个"""
    client = get_client()
    headers = build_headers(target_uid, biz_id, device)
    uids = []
    offset = 0
    while len(uids) < limit:
        params = {"offset": offset, "limit": FOLLOWERS_PAGE_SIZE}
        response = client.get(FOLLOWERS_URL, params=params, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"查询粉丝列表失败: HTTP {response.status_code}: {response.text[:200]}")
        result = response.json()
        if result.get("errorCode") != 0:
            raise RuntimeError(f"查询粉丝列表失败: errorCode={result.get('errorCode')}, errorMessage={result.get('errorMessage')}")

        data = result.get("data") or {}
        page = data.get("list") or []
        uids.extend(item["uid"] for item in page)
        offset += len(page)
        if not page or offset >= data.get("count", 0):
            break

    logger.info(f"用户 {target_uid} 粉丝查询到 {len(uids)} 个")
    return uids[:limit]


def follow_modify(uid, target_uid, follow, biz_id, device):
    headers = build_headers(uid, biz_id, device)
    payload = {"targetUid": target_uid, "follow": follow}
    try:
        response = get_client().post(FOLLOW_URL, json=payload, headers=headers)
    except Exception as e:
        return uid, False, f"请求异常: {e}"

    if response.status_code != 200:
        return uid, False, f"HTTP {response.status_code}: {response.text[:200]}"
    try:
        result = response.json()
    except ValueError:
        return uid, False, f"响应非JSON: {response.text[:200]}"
    if result.get("errorCode") != 0:
        return uid, False, f"errorCode={result.get('errorCode')}, errorMessage={result.get('errorMessage')}"
    return uid, True, "ok"


def pick_uids(args):
    if args.uids:
        uids = [int(item.strip()) for item in args.uids.split(",") if item.strip()]
        return [uid for uid in uids if uid != args.target]

    if args.unfollow:
        return fetch_followers(args.target, args.count, args.biz_id, args.device)

    pool = [uid for uid in range(args.start, args.end + 1) if uid != args.target]
    if args.count > len(pool):
        raise ValueError(f"区间 {args.start}-{args.end} 可用用户只有 {len(pool)} 个，无法满足 count={args.count}")
    return random.sample(pool, args.count)


def batch_follow(target_uid, uids, follow, concurrency, biz_id, device):
    action = "关注" if follow else "取消关注"
    logger.info(f"开始批量{action}: 目标 {target_uid}，用户数 {len(uids)}，并发 {concurrency}")
    start_time = time.time()

    success_uids, failures = [], []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(follow_modify, uid, target_uid, follow, biz_id, device) for uid in uids]
        for future in as_completed(futures):
            uid, ok, msg = future.result()
            if ok:
                success_uids.append(uid)
            else:
                failures.append((uid, msg))
                logger.error(f"用户 {uid} {action} {target_uid} 失败: {msg}")

    elapsed = time.time() - start_time
    logger.info(f"\n========== 批量{action}完成 ==========")
    logger.info(f"目标用户: {target_uid}，成功 {len(success_uids)}/{len(uids)}，失败 {len(failures)}，耗时 {elapsed:.2f}s")
    logger.info(f"成功用户: {','.join(str(uid) for uid in sorted(success_uids))}")
    if failures:
        logger.info(f"失败用户: {','.join(str(uid) for uid, _ in sorted(failures))}")
    return success_uids, failures


def main():
    parser = argparse.ArgumentParser(description="批量关注/取消关注工具")
    parser.add_argument("-t", "--target", type=int, required=True, help="目标用户ID（被关注的人）")
    parser.add_argument("-c", "--count", type=int, default=10, help="关注：随机抽取的关注者数量；取消关注：取消的粉丝数量（不足则全部）。默认10")
    parser.add_argument("--unfollow", action="store_true", help="取消关注（默认是关注），会先查询目标用户的粉丝列表")
    parser.add_argument("--uids", help="指定关注者ID，多个用逗号分隔；指定后忽略 --count/--start/--end，取消关注时也不再查粉丝列表")
    parser.add_argument("--start", type=int, default=10001, help="随机token区间起始，默认10001")
    parser.add_argument("--end", type=int, default=10600, help="随机token区间结束，默认10600")
    parser.add_argument("--concurrency", type=int, default=20, help="并发数，默认20")
    parser.add_argument("--biz-id", default=DEFAULT_BIZ_ID, help=f"BizId 请求头，默认{DEFAULT_BIZ_ID}")
    parser.add_argument("--device", default=DEFAULT_D, help=f"d 请求头，默认{DEFAULT_D}")
    args = parser.parse_args()

    if args.target <= 0:
        parser.error("--target 必须大于0")
    if args.count <= 0:
        parser.error("--count 必须大于0")
    if args.concurrency <= 0:
        parser.error("--concurrency 必须大于0")
    if args.start > args.end:
        parser.error("--start 不能大于 --end")

    try:
        uids = pick_uids(args)
    except ValueError as e:
        parser.error(str(e))
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    if not uids:
        logger.info(f"用户 {args.target} 没有可处理的粉丝/关注者，结束")
        return

    batch_follow(args.target, uids, not args.unfollow, args.concurrency, args.biz_id, args.device)


if __name__ == "__main__":
    main()
