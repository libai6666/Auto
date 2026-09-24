import argparse
import json
import math
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.client_factory import ClientFactory
from utils.logger import logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
JOIN_URL = "/api/game/roulette/v1/join"
BET_URL = "/api/game/roulette/v1/bet"


@dataclass
class WorkerSummary:
    user_id: str
    total: int = 0
    success: int = 0
    failures: int = 0
    latencies_ms: list = field(default_factory=list)
    http_statuses: Counter = field(default_factory=Counter)
    business_codes: Counter = field(default_factory=Counter)
    error_samples: list = field(default_factory=list)


def parse_args():
    parser = argparse.ArgumentParser(description="roulette bet 压测脚本")
    parser.add_argument("--user-count", type=int, default=5, help="使用 users.yaml 中前 N 个手机号账号参与压测")
    parser.add_argument("--user-ids", help="指定参与压测的用户ID，多个用逗号分隔，例如 user1,user2,user3")
    parser.add_argument("--rounds", type=int, default=10, help="每个账号执行 bet 的次数")
    parser.add_argument("--total-requests", type=int, help="总请求数，会平均分配到所有参与账号")
    parser.add_argument("--bet-number", type=int, default=1, help="押注数字")
    parser.add_argument("--coin-amount", type=int, default=100, help="每次押注金币")
    parser.add_argument("--room-id", default="", help="房间ID，默认空字符串")
    parser.add_argument("--interval-ms", type=int, default=0, help="同一账号两次 bet 之间的间隔毫秒数")
    parser.add_argument("--concurrency", type=int, default=1, help="每个账号的并发线程数（默认1）")
    parser.add_argument("--target-qps", type=int, default=0, help="目标每秒请求数（0=不限速，尽可能快）")
    parser.add_argument("--duration", type=int, default=0, help="持续压测时间（秒），设置后忽略 --rounds 和 --total-requests")
    parser.add_argument("--skip-join", action="store_true", help="跳过 join，直接压测 bet")
    parser.add_argument("--log-all-bets", action="store_true", help="打印每一次 bet 的请求和响应详情，默认只打印 join、首个 bet 和失败 bet")
    parser.add_argument("--output", help="将汇总结果写入 JSON 文件")
    return parser.parse_args()


def validate_args(args):
    if args.user_count <= 0:
        raise ValueError("--user-count 必须大于 0")
    if args.rounds <= 0:
        raise ValueError("--rounds 必须大于 0")
    if args.total_requests is not None and args.total_requests <= 0:
        raise ValueError("--total-requests 必须大于 0")
    if not 1 <= args.bet_number <= 8:
        raise ValueError("--bet-number 必须在 1 到 8 之间")
    if args.coin_amount <= 0:
        raise ValueError("--coin-amount 必须大于 0")
    if args.interval_ms < 0:
        raise ValueError("--interval-ms 不能小于 0")
    if args.concurrency <= 0:
        raise ValueError("--concurrency 必须大于 0")
    if args.target_qps < 0:
        raise ValueError("--target-qps 不能小于 0")
    if args.duration < 0:
        raise ValueError("--duration 不能小于 0")


def get_available_user_ids(factory):
    available_user_ids = []
    for user_id, user_config in factory.user_configs.items():
        if user_config.get("phoneNumber") and user_config.get("phoneCode"):
            available_user_ids.append(user_id)
    return available_user_ids


def resolve_user_ids(factory, args):
    available_user_ids = get_available_user_ids(factory)
    if not available_user_ids:
        raise ValueError("users.yaml 中没有可用的手机号账号")

    if args.user_ids:
        requested_user_ids = [item.strip() for item in args.user_ids.split(",") if item.strip()]
        if not requested_user_ids:
            raise ValueError("--user-ids 不能为空")
        missing_user_ids = [user_id for user_id in requested_user_ids if user_id not in available_user_ids]
        if missing_user_ids:
            raise ValueError(f"以下用户不存在或不是手机号账号: {', '.join(missing_user_ids)}")
        return requested_user_ids

    if args.user_count > len(available_user_ids):
        raise ValueError(f"可用手机号账号只有 {len(available_user_ids)} 个，无法满足 user-count={args.user_count}")

    return available_user_ids[:args.user_count]


def build_request_plan(total_requests, rounds, user_ids):
    if total_requests is None:
        return {user_id: rounds for user_id in user_ids}

    base_count, remainder = divmod(total_requests, len(user_ids))
    request_plan = {}
    for index, user_id in enumerate(user_ids):
        request_plan[user_id] = base_count + (1 if index < remainder else 0)
    return request_plan


def build_url(client, path):
    if path.startswith(("http://", "https://")):
        return path
    return f"{client.base_url}{path}"


def format_log_value(value):
    if value is None:
        return "null"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def mask_header_value(key, value):
    if key.lower() != "authorization":
        return value
    value = str(value)
    if len(value) <= 20:
        return "*" * len(value)
    return f"{value[:10]}...{value[-10:]}"


def build_headers_for_log(client):
    return {key: mask_header_value(key, value) for key, value in dict(client.session.headers).items()}


def extract_response_body(response):
    try:
        return response.json()
    except Exception:
        return response.text


def log_api_request(user_id, api_name, client, method, path, payload):
    logger.info(
        f"\n==================== {api_name} REQUEST ====================\n"
        f"User: {user_id}\n"
        f"Method: {method}\n"
        f"URL: {build_url(client, path)}\n"
        f"Headers: {format_log_value(build_headers_for_log(client))}\n"
        f"JSON: {format_log_value(payload)}\n"
    )


def log_api_response(user_id, api_name, response, elapsed_ms):
    logger.info(
        f"\n==================== {api_name} RESPONSE ===================\n"
        f"User: {user_id}\n"
        f"Status Code: {response.status_code}\n"
        f"Time Taken: {elapsed_ms:.2f} ms\n"
        f"Headers: {format_log_value(dict(response.headers))}\n"
        f"Response Body: {format_log_value(extract_response_body(response))}\n"
    )


def request_json(client, method, path, payload=None, user_id=None, api_name=None, log_details=False):
    url = build_url(client, path)
    request_name = api_name or path
    request_user = user_id or "unknown"

    if log_details:
        log_api_request(request_user, request_name, client, method, path, payload)

    started_at = time.perf_counter()
    try:
        response = client.session.request(
            method=method,
            url=url,
            json=payload,
            timeout=client.timeout,
            verify=client.verify_ssl,
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        if log_details:
            logger.error(
                f"\n==================== {request_name} EXCEPTION ==================\n"
                f"User: {request_user}\n"
                f"Time Taken: {elapsed_ms:.2f} ms\n"
                f"Request Body: {format_log_value(payload)}\n"
                f"Exception: {exc}\n"
            )
        raise

    if log_details:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        log_api_response(request_user, request_name, response, elapsed_ms)

    return response


def parse_response(response):
    try:
        data = response.json()
    except Exception:
        data = {"rawText": response.text}

    if isinstance(data, dict):
        error_code = data.get("errorCode")
        error_message = data.get("errorMessage") or data.get("message") or ""
    else:
        error_code = "NON_JSON"
        error_message = str(data)

    success = response.status_code == 200 and isinstance(data, dict) and data.get("errorCode") == 0
    return success, data, error_code, error_message


def requires_rejoin(error_code, error_message):
    normalized_code = str(error_code) if error_code is not None else ""
    normalized_message = str(error_message or "").lower()
    return normalized_code == "109000" or "failed to join the game" in normalized_message


def join_roulette(client, user_id, api_name="ROULETTE_JOIN", log_details=True):
    join_response = request_json(
        client,
        "POST",
        JOIN_URL,
        user_id=user_id,
        api_name=api_name,
        log_details=log_details,
    )
    join_success, join_data, error_code, error_message = parse_response(join_response)
    return join_response, join_success, join_data, error_code, error_message


def login_and_prepare_clients(factory, user_ids, skip_join):
    prepared_clients = []
    skipped_users = []

    for user_id in user_ids:
        client = factory.get_client(user_id, auto_heartbeat=False)
        if not client:
            skipped_users.append({"userId": user_id, "stage": "create_client", "reason": "无法创建客户端"})
            continue

        login_start = time.perf_counter()
        login_success = client.login()
        login_cost_ms = round((time.perf_counter() - login_start) * 1000, 2)

        if not login_success:
            skipped_users.append({"userId": user_id, "stage": "login", "reason": f"登录失败，耗时 {login_cost_ms} ms"})
            continue

        if not skip_join:
            join_start = time.perf_counter()
            try:
                join_response, join_success, join_data, error_code, error_message = join_roulette(
                    client,
                    user_id=user_id,
                    api_name="ROULETTE_JOIN",
                    log_details=True,
                )
                join_cost_ms = round((time.perf_counter() - join_start) * 1000, 2)
                if not join_success:
                    skipped_users.append(
                        {
                            "userId": user_id,
                            "stage": "join",
                            "reason": f"HTTP {join_response.status_code}, errorCode={error_code}, errorMessage={error_message}, 耗时 {join_cost_ms} ms",
                            "response": join_data,
                        }
                    )
                    continue
            except Exception as exc:
                join_cost_ms = round((time.perf_counter() - join_start) * 1000, 2)
                skipped_users.append({"userId": user_id, "stage": "join", "reason": f"请求异常: {exc}, 耗时 {join_cost_ms} ms"})
                continue

        prepared_clients.append((user_id, client))

    return prepared_clients, skipped_users


class RateLimiter:
    """Token bucket rate limiter for controlling QPS."""

    def __init__(self, target_qps):
        self.enabled = target_qps > 0
        if self.enabled:
            self.interval = 1 / target_qps
        else:
            self.interval = 0
        self._lock = threading.Lock()
        self._last_time = time.perf_counter()

    def wait(self, stop_event=None):
        if not self.enabled:
            return True
        with self._lock:
            now = time.perf_counter()
            wait_until = self._last_time + self.interval
            if now < wait_until:
                sleep_seconds = wait_until - now
                if stop_event is not None:
                    if stop_event.wait(sleep_seconds):
                        return False
                else:
                    time.sleep(sleep_seconds)
            self._last_time = max(time.perf_counter(), wait_until)
        return True


class RejoinController:
    def __init__(self, client, user_id):
        self.client = client
        self.user_id = user_id
        self._lock = threading.Lock()
        self._join_version = 0
        self.rejoin_count = 0

    def get_version(self):
        with self._lock:
            return self._join_version

    def rejoin_if_needed(self, observed_version, request_label):
        with self._lock:
            if self._join_version != observed_version:
                return True, self._join_version, False

            logger.warning(
                f"检测到需要重新加入游戏，开始自动 rejoin。User: {self.user_id}, Request Index: {request_label}"
            )
            join_response, join_success, join_data, error_code, error_message = join_roulette(
                self.client,
                user_id=self.user_id,
                api_name=f"ROULETTE_REJOIN[{request_label}]",
                log_details=True,
            )
            if join_success:
                self._join_version += 1
                self.rejoin_count += 1
                logger.info(
                    f"自动 rejoin 成功。User: {self.user_id}, Request Index: {request_label}, Join Version: {self._join_version}"
                )
                return True, self._join_version, True

            logger.error(
                f"自动 rejoin 失败。User: {self.user_id}, Request Index: {request_label}, "
                f"HTTP {join_response.status_code}, errorCode={error_code}, errorMessage={error_message}, "
                f"Response Body: {format_log_value(join_data)}"
            )
            return False, self._join_version, True


def _record_bet_result(summary, user_id, bet_payload, request_index, request_label, response, latency_ms, log_details):
    success, response_data, error_code, error_message = parse_response(response)

    summary.total += 1
    summary.latencies_ms.append(latency_ms)
    summary.http_statuses[str(response.status_code)] += 1
    summary.business_codes[str(error_code)] += 1

    if success:
        summary.success += 1
    else:
        summary.failures += 1
        if not log_details:
            logger.warning(
                f"\n==================== ROULETTE_BET FAILURE ==================\n"
                f"User: {user_id}\n"
                f"Request Index: {request_label}\n"
                f"Request Body: {format_log_value(bet_payload)}\n"
                f"Status Code: {response.status_code}\n"
                f"Time Taken: {latency_ms:.2f} ms\n"
                f"Response Body: {format_log_value(response_data)}\n"
            )
        if len(summary.error_samples) < 5:
            summary.error_samples.append(
                {
                    "httpStatus": response.status_code,
                    "errorCode": error_code,
                    "errorMessage": error_message,
                    "response": response_data,
                }
            )


def _record_bet_exception(summary, user_id, bet_payload, request_label, exc, latency_ms, log_details):
    summary.total += 1
    summary.failures += 1
    summary.latencies_ms.append(latency_ms)
    summary.http_statuses["EXCEPTION"] += 1
    summary.business_codes["EXCEPTION"] += 1
    if not log_details:
        logger.error(
            f"\n==================== ROULETTE_BET EXCEPTION ==================\n"
            f"User: {user_id}\n"
            f"Request Index: {request_label}\n"
            f"Request Body: {format_log_value(bet_payload)}\n"
            f"Time Taken: {latency_ms:.2f} ms\n"
            f"Exception: {exc}\n"
        )
    if len(summary.error_samples) < 5:
        summary.error_samples.append({"exception": str(exc)})


def run_bet_worker(user_id, client, request_count, barrier, bet_number, coin_amount, room_id, interval_ms, log_all_bets,
                   rate_limiter=None, stop_event=None, thread_index=0, rejoin_controller=None):
    summary = WorkerSummary(user_id=user_id)
    join_version = rejoin_controller.get_version() if rejoin_controller else 0

    try:
        barrier.wait(timeout=30)
    except threading.BrokenBarrierError:
        summary.error_samples.append("并发启动失败：屏障已损坏")
        return summary

    duration_mode = stop_event is not None
    request_index = 0

    while True:
        if duration_mode:
            if stop_event.is_set():
                break
        else:
            if request_index >= request_count:
                break

        if rate_limiter:
            if not rate_limiter.wait(stop_event=stop_event if duration_mode else None):
                break

        if duration_mode and stop_event.is_set():
            break

        request_index += 1
        bet_payload = {
            "roomId": room_id,
            "number": bet_number,
            "coinAmount": coin_amount,
        }
        request_label = f"T{thread_index}-{request_index}" if duration_mode else f"{request_index}/{request_count}"
        log_details = log_all_bets or (request_index == 1 and thread_index == 0)
        started_at = time.perf_counter()
        try:
            response = request_json(
                client,
                "POST",
                BET_URL,
                bet_payload,
                user_id=user_id,
                api_name=f"ROULETTE_BET[{request_label}]",
                log_details=log_details,
            )
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            success, _, error_code, error_message = parse_response(response)
            if not success and rejoin_controller and requires_rejoin(error_code, error_message):
                rejoin_success, join_version, did_rejoin = rejoin_controller.rejoin_if_needed(join_version, request_label)
                if rejoin_success:
                    retry_log_details = log_details or did_rejoin
                    try:
                        retry_response = request_json(
                            client,
                            "POST",
                            BET_URL,
                            bet_payload,
                            user_id=user_id,
                            api_name=f"ROULETTE_BET_RETRY[{request_label}]",
                            log_details=retry_log_details,
                        )
                        total_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                        _record_bet_result(
                            summary,
                            user_id,
                            bet_payload,
                            request_index,
                            f"{request_label}-retry",
                            retry_response,
                            total_latency_ms,
                            retry_log_details,
                        )
                        continue
                    except Exception as exc:
                        total_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                        _record_bet_exception(
                            summary,
                            user_id,
                            bet_payload,
                            f"{request_label}-retry",
                            exc,
                            total_latency_ms,
                            retry_log_details,
                        )
                        continue

                latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

            _record_bet_result(summary, user_id, bet_payload, request_index, request_label, response, latency_ms, log_details)
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            _record_bet_exception(summary, user_id, bet_payload, request_label, exc, latency_ms, log_details)

        if interval_ms > 0 and not (duration_mode and stop_event.is_set()):
            time.sleep(interval_ms / 1000)

    return summary


def percentile(values, p):
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])

    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * (p / 100)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[int(index)])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    return float(lower_value + (upper_value - lower_value) * (index - lower))


def merge_worker_summaries(worker_summaries, test_duration_seconds):
    all_latencies = []
    http_statuses = Counter()
    business_codes = Counter()
    error_samples = []
    total = 0
    success = 0
    failures = 0

    for worker_summary in worker_summaries:
        total += worker_summary.total
        success += worker_summary.success
        failures += worker_summary.failures
        all_latencies.extend(worker_summary.latencies_ms)
        http_statuses.update(worker_summary.http_statuses)
        business_codes.update(worker_summary.business_codes)
        for sample in worker_summary.error_samples:
            if len(error_samples) < 10:
                error_samples.append({"userId": worker_summary.user_id, "detail": sample})

    avg_latency = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0.0
    qps = round(total / test_duration_seconds, 2) if test_duration_seconds > 0 else 0.0
    success_rate = round(success / total * 100, 2) if total > 0 else 0.0

    return {
        "totalRequests": total,
        "successRequests": success,
        "failedRequests": failures,
        "successRate": success_rate,
        "qps": qps,
        "avgLatencyMs": avg_latency,
        "minLatencyMs": round(min(all_latencies), 2) if all_latencies else 0.0,
        "p50LatencyMs": round(percentile(all_latencies, 50), 2) if all_latencies else 0.0,
        "p95LatencyMs": round(percentile(all_latencies, 95), 2) if all_latencies else 0.0,
        "p99LatencyMs": round(percentile(all_latencies, 99), 2) if all_latencies else 0.0,
        "maxLatencyMs": round(max(all_latencies), 2) if all_latencies else 0.0,
        "httpStatusDistribution": dict(http_statuses),
        "businessCodeDistribution": dict(business_codes),
        "errorSamples": error_samples,
    }


def save_output(path, content):
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(content, file, ensure_ascii=False, indent=2)


def main():
    args = parse_args()
    validate_args(args)

    factory = ClientFactory()
    selected_user_ids = resolve_user_ids(factory, args)

    duration_mode = args.duration > 0
    concurrency = args.concurrency
    target_qps = args.target_qps

    if duration_mode:
        request_plan = {uid: 0 for uid in selected_user_ids}
        logger.info(f"压测模式: 持续 {args.duration} 秒")
    else:
        request_plan = build_request_plan(args.total_requests, args.rounds, selected_user_ids)

    logger.info(f"本次计划使用用户: {selected_user_ids}")
    if not duration_mode:
        logger.info(f"每个用户请求分配: {request_plan}")
    logger.info(
        f"bet 配置: number={args.bet_number}, coinAmount={args.coin_amount}, roomId='{args.room_id}', intervalMs={args.interval_ms}"
    )
    logger.info(f"并发配置: concurrency={concurrency}, targetQps={target_qps}, duration={args.duration}s")
    logger.info(f"日志配置: logAllBets={args.log_all_bets}")

    prepared_clients, skipped_users = login_and_prepare_clients(factory, selected_user_ids, args.skip_join)

    if not prepared_clients:
        raise SystemExit("没有可用于压测的账号，请检查登录和 join 是否成功")

    rejoin_controllers = {user_id: RejoinController(client, user_id) for user_id, client in prepared_clients}
    worker_configs = []
    for user_id, client in prepared_clients:
        planned_count = request_plan.get(user_id, 0)
        if duration_mode:
            for t_idx in range(concurrency):
                worker_configs.append((user_id, client, 0, t_idx, rejoin_controllers[user_id]))
            continue

        base_count, remainder = divmod(planned_count, concurrency)
        for t_idx in range(concurrency):
            thread_request_count = base_count + (1 if t_idx < remainder else 0)
            if thread_request_count > 0:
                worker_configs.append((user_id, client, thread_request_count, t_idx, rejoin_controllers[user_id]))

    if not worker_configs:
        raise SystemExit("请求计划为空，没有实际要执行的 bet 请求")

    total_threads = len(worker_configs)
    rate_limiter = RateLimiter(target_qps) if target_qps > 0 else None
    stop_event = threading.Event() if duration_mode else None
    barrier = threading.Barrier(total_threads)
    started_at = time.perf_counter()
    worker_summaries = []

    with ThreadPoolExecutor(max_workers=total_threads) as executor:
        future_to_label = {}
        for user_id, client, request_count, t_idx, rejoin_controller in worker_configs:
            future = executor.submit(
                run_bet_worker,
                user_id,
                client,
                request_count,
                barrier,
                args.bet_number,
                args.coin_amount,
                args.room_id,
                args.interval_ms,
                args.log_all_bets,
                rate_limiter,
                stop_event,
                t_idx,
                rejoin_controller,
            )
            future_to_label[future] = f"{user_id}-T{t_idx}"

        if duration_mode:
            logger.info(f"压测已启动，将持续 {args.duration} 秒 ...")
            time.sleep(args.duration)
            stop_event.set()
            logger.info("已发送停止信号，等待线程结束 ...")

        for future in as_completed(future_to_label):
            label = future_to_label[future]
            try:
                worker_summaries.append(future.result())
            except Exception as exc:
                logger.error(f"线程 {label} 执行 bet 压测时发生异常: {exc}")
                worker_summaries.append(
                    WorkerSummary(
                        user_id=label,
                        total=0,
                        success=0,
                        failures=0,
                        latencies_ms=[],
                        http_statuses=Counter({"EXCEPTION": 1}),
                        business_codes=Counter({"EXCEPTION": 1}),
                        error_samples=[{"exception": str(exc)}],
                    )
                )

    test_duration_seconds = round(time.perf_counter() - started_at, 4)
    merged_summary = merge_worker_summaries(worker_summaries, test_duration_seconds)
    rejoin_counts = {user_id: controller.rejoin_count for user_id, controller in rejoin_controllers.items()}

    result = {
        "baseUrl": prepared_clients[0][1].base_url,
        "joinEnabled": not args.skip_join,
        "selectedUsers": selected_user_ids,
        "preparedUsers": [user_id for user_id, _ in prepared_clients],
        "skippedUsers": skipped_users,
        "rejoinCounts": rejoin_counts,
        "requestPlan": request_plan,
        "betConfig": {
            "number": args.bet_number,
            "coinAmount": args.coin_amount,
            "roomId": args.room_id,
            "intervalMs": args.interval_ms,
        },
        "concurrencyConfig": {
            "concurrency": concurrency,
            "targetQps": target_qps,
            "duration": args.duration,
        },
        "testDurationSeconds": test_duration_seconds,
        "summary": merged_summary,
    }

    logger.info("=" * 80)
    logger.info(f"压测完成，总耗时: {test_duration_seconds} s")
    logger.info(f"参与压测账号数: {len(prepared_clients)}, 并发线程数: {total_threads}")
    logger.info(f"目标QPS: {target_qps if target_qps > 0 else '不限速'}")
    logger.info(f"总请求数: {merged_summary['totalRequests']}")
    logger.info(f"成功请求数: {merged_summary['successRequests']}")
    logger.info(f"失败请求数: {merged_summary['failedRequests']}")
    logger.info(f"成功率: {merged_summary['successRate']}%")
    logger.info(f"QPS: {merged_summary['qps']}")
    logger.info(f"平均耗时: {merged_summary['avgLatencyMs']} ms")
    logger.info(f"P50: {merged_summary['p50LatencyMs']} ms")
    logger.info(f"P95: {merged_summary['p95LatencyMs']} ms")
    logger.info(f"P99: {merged_summary['p99LatencyMs']} ms")
    logger.info(f"HTTP 状态分布: {merged_summary['httpStatusDistribution']}")
    logger.info(f"业务码分布: {merged_summary['businessCodeDistribution']}")
    logger.info(f"自动rejoin次数: {rejoin_counts}")
    if skipped_users:
        logger.warning(f"跳过的账号: {skipped_users}")
    if merged_summary["errorSamples"]:
        logger.warning(f"错误样例: {merged_summary['errorSamples']}")
    logger.info("=" * 80)

    if args.output:
        save_output(args.output, result)
        logger.info(f"压测结果已写入: {args.output}")


if __name__ == "__main__":
    main()
