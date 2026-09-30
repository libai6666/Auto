#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设置用户等级脚本
功能：调用运营操作接口，将指定用户设置为目标等级（scene 即目标等级），设置后查询用户资料校验 userLevel
示例：
    # 把 10017 设置为 6 级
    python scripts/set_user_level.py -u 10017 -l 6
    # 批量把多个用户设置为 10 级
    python scripts/set_user_level.py -u 10017,10018,10019 -l 10
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib3

from utils.api_client import APIClient
from utils.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPERATE_URL = "/api/user/v1/operate/submit"
USER_INFO_URL = "/api/user/v1/user/info"
OPERATE_NAME = "admin"
OPERATE = "用户等级设置"
DEFAULT_BIZ_ID = "7"
DEFAULT_D = "123456"


def build_headers(uid, biz_id, device):
    return {
        "token": str(uid),
        "BizId": str(biz_id),
        "d": str(device),
    }


def get_user_level(client, uid, biz_id, device):
    """查询用户当前等级，失败返回 None"""
    try:
        response = client.get(
            USER_INFO_URL,
            params={"uid": uid, "targetId": uid},
            headers=build_headers(uid, biz_id, device),
        )
        result = response.json()
    except Exception as e:
        logger.error(f"查询用户 {uid} 资料异常: {e}")
        return None
    if response.status_code != 200 or result.get("errorCode") != 0:
        logger.error(f"查询用户 {uid} 资料失败: {response.text[:200]}")
        return None
    return (result.get("data") or {}).get("userLevel")


def set_user_level(client, uid, level):
    """设置用户等级，返回 (是否成功, 信息)"""
    payload = {
        "operateName": OPERATE_NAME,
        "operate": OPERATE,
        "uid": uid,
        "scene": level,
    }
    try:
        response = client.post(OPERATE_URL, json=payload)
    except Exception as e:
        return False, f"请求异常: {e}"
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}: {response.text[:200]}"
    try:
        result = response.json()
    except ValueError:
        return False, f"响应非JSON: {response.text[:200]}"
    if result.get("errorCode") != 0:
        return False, f"errorCode={result.get('errorCode')}, errorMessage={result.get('errorMessage')}"
    return True, (result.get("data") or {}).get("jsonValue", "ok")


def main():
    parser = argparse.ArgumentParser(description="设置用户等级工具")
    parser.add_argument("-u", "--uids", required=True, help="用户ID，多个用逗号分隔")
    parser.add_argument("-l", "--level", type=int, required=True, help="目标等级（即接口参数 scene）")
    parser.add_argument("--biz-id", default=DEFAULT_BIZ_ID, help=f"查询用户资料时的 BizId 请求头，默认{DEFAULT_BIZ_ID}")
    parser.add_argument("--device", default=DEFAULT_D, help=f"查询用户资料时的 d 请求头，默认{DEFAULT_D}")
    args = parser.parse_args()

    try:
        uids = [int(item.strip()) for item in args.uids.split(",") if item.strip()]
    except ValueError:
        parser.error("--uids 必须是逗号分隔的数字")
    if not uids:
        parser.error("--uids 不能为空")
    if args.level <= 0:
        parser.error("--level 必须大于0")

    client = APIClient()
    results = []
    for uid in uids:
        before = get_user_level(client, uid, args.biz_id, args.device)
        ok, msg = set_user_level(client, uid, args.level)
        after = get_user_level(client, uid, args.biz_id, args.device) if ok else before
        verified = ok and after == args.level
        results.append((uid, ok, verified, before, after, msg))
        if not ok:
            logger.error(f"用户 {uid} 设置等级失败: {msg}")
        elif not verified:
            logger.warning(f"用户 {uid} 接口返回成功，但查询到的等级为 {after}，目标 {args.level}，接口返回: {msg}")

    logger.info("\n========== 设置用户等级完成 ==========")
    for uid, ok, verified, before, after, msg in results:
        status = "成功" if verified else ("接口成功但等级未变" if ok else "失败")
        logger.info(f"用户 {uid}: {before} -> {after}（目标 {args.level}）{status}")
    success = sum(1 for r in results if r[2])
    logger.info(f"成功 {success}/{len(results)}")


if __name__ == "__main__":
    main()
