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
    # 正式环境：让 8387289 关注 9011365（默认通过mockRefresh获取真实token）
    python scripts/batch_follow.py --env prod -t 9011365 --uids 8387289
    # 正式环境：从默认区间 4000000-4000100 随机抽 50 个关注 9011365
    python scripts/batch_follow.py --env prod -t 9011365 -c 10
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
from utils.app.api.user import UserAPI
from utils.data_handler import load_config
from utils.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOLLOW_URL = "/api/user/v1/relation/follow/modify"
FOLLOWERS_URL = "/api/user/v1/relation/followers"
FOLLOWERS_PAGE_SIZE = 50
DEFAULT_BIZ_ID = "7"
DEFAULT_D = "123456"
DEFAULT_COUNTRY = "IN"
DEFAULT_ROLE_LEVEL = 3  # 角色：1 用户、3 主播、5 代理

# mockRefresh/正式环境请求的公共头，与 batch_apply_tribe.MockUserClient 保持一致
MOCK_COMMON_HEADERS = {"d": "111", "p": "1", "v": "5.8.1", "l": "zh-en", "appName": "duoo"}

# 各环境默认随机uid区间
ENV_UID_RANGE = {"dev": (10001, 10600), "test": (10001, 10600), "prod": (4000000, 4000600)}

_thread_local = threading.local()
_BASE_URL = None
_MOCK = None  # {"country":..., "roleLevel":...}，None表示使用uid作为token（测试环境）
_token_cache = {}
_token_lock = threading.Lock()


def get_client():
    client = getattr(_thread_local, "client", None)
    if client is None:
        client = APIClient(base_url=_BASE_URL)
        if _MOCK:
            client.session.headers.update(MOCK_COMMON_HEADERS)
        _thread_local.client = client
    return client


def mock_refresh_token(uid):
    """通过mockRefresh接口获取uid的真实token（带缓存）"""
    with _token_lock:
        if uid in _token_cache:
            return _token_cache[uid]
    success, token, _ = UserAPI.mock_refresh(
        get_client(), uid, country=_MOCK["country"], role_level=_MOCK["roleLevel"]
    )
    if not success or not token:
        raise RuntimeError(f"mockRefresh失败: uid={uid}")
    with _token_lock:
        _token_cache[uid] = token
    return token


def auth_token(uid):
    """mock模式返回真实token，否则返回None（用uid当token）"""
    return mock_refresh_token(uid) if _MOCK else None


def build_headers(uid, biz_id, device, token=None):
    headers = {"BizId": str(biz_id)}
    if token:
        # mock模式：d必须与mockRefresh签发token时的deviceId一致，否则网关401
        headers["Authorization"] = token
        headers["d"] = MOCK_COMMON_HEADERS["d"]
    else:
        headers["token"] = str(uid)
        headers["d"] = str(device)
    return headers


def fetch_followers(target_uid, limit, biz_id, device):
    """查询目标用户的粉丝uid列表，最多返回 limit 个"""
    client = get_client()
    headers = build_headers(target_uid, biz_id, device, auth_token(target_uid))
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
    payload = {"targetUid": target_uid, "follow": follow}
    try:
        headers = build_headers(uid, biz_id, device, auth_token(uid))
    except Exception as e:
        return uid, False, str(e)
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
    parser.add_argument("--start", type=int, default=None, help="随机uid区间起始，默认按环境：test/dev为10001，prod为4000000")
    parser.add_argument("--end", type=int, default=None, help="随机uid区间结束，默认按环境：test/dev为10600，prod为4000100")
    parser.add_argument("--concurrency", type=int, default=10, help="并发数，默认10")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="test", help="执行环境，默认test")
    parser.add_argument("--mock", dest="mock", action="store_true", default=True, help="通过mockRefresh接口获取真实token，默认开启")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="不走mockRefresh，直接用uid当token")
    parser.add_argument("--country", default=DEFAULT_COUNTRY, help=f"mockRefresh的country，默认{DEFAULT_COUNTRY}")
    parser.add_argument("--role-level", type=int, default=DEFAULT_ROLE_LEVEL, help=f"mockRefresh的roleLevel：1用户、3主播、5代理，默认{DEFAULT_ROLE_LEVEL}")
    parser.add_argument("--biz-id", default=DEFAULT_BIZ_ID, help=f"BizId 请求头，默认{DEFAULT_BIZ_ID}")
    parser.add_argument("--device", default=DEFAULT_D, help=f"d 请求头，默认{DEFAULT_D}（mock模式固定使用{MOCK_COMMON_HEADERS['d']}与mockRefresh保持一致）")
    args = parser.parse_args()

    config = load_config()
    env = args.env or config.get("current_env", "test")
    base_url = (config.get("env_config", {}).get(env) or {}).get("base_url")
    if not base_url:
        parser.error(f"环境 {env} 未配置 base_url")
    global _BASE_URL, _MOCK
    _BASE_URL = base_url
    logger.info(f"执行环境: {env} ({base_url})")
    if args.mock:
        _MOCK = {"country": args.country, "roleLevel": args.role_level}
        logger.info(f"mockRefresh模式: country={args.country}, roleLevel={args.role_level}")
    else:
        logger.info("未开启mockRefresh，使用uid作为token")

    default_start, default_end = ENV_UID_RANGE.get(env, ENV_UID_RANGE["test"])
    if args.start is None:
        args.start = default_start
    if args.end is None:
        args.end = default_end
    logger.info(f"随机uid区间: {args.start}-{args.end}")

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
