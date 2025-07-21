#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
心跳管理模块
"""

import threading
import time
from utils.logger import logger
from utils.app.api.online import OnlineAPI


class HeartbeatThread(threading.Thread):
    """
    心跳线程，负责定期发送心跳
    """
    
    def __init__(self, client, interval=10, daemon=True):
        """
        初始化心跳线程
        :param client: API客户端实例
        :param interval: 心跳间隔（秒），默认10秒
        :param daemon: 是否为守护线程，默认为True
        """
        super().__init__(daemon=daemon)
        self.client = client
        self.interval = interval
        self._stop_event = threading.Event()
        self._is_running = False
        self._last_heartbeat_time = 0
        self._last_heartbeat_success = False
        self._last_status_check = False
        self._lock = threading.RLock()
        self.name = f"Heartbeat-{client.get_user_id() or 'Unknown'}"
    
    def run(self):
        """
        线程运行方法
        """
        logger.info(f"心跳线程启动，间隔: {self.interval}秒")
        self._is_running = True
        
        try:
            # 立即发送第一次心跳
            self._send_heartbeat()
            
            # 循环发送心跳
            while not self._stop_event.is_set():
                # 等待一段时间，但可以随时停止
                if self._stop_event.wait(self.interval):
                    break
                
                # 发送心跳
                self._send_heartbeat()
        except Exception as e:
            logger.error(f"心跳线程异常: {str(e)}")
        finally:
            self._is_running = False
            logger.info("心跳线程已停止")
    
    def _send_heartbeat(self):
        """
        发送心跳并检查状态
        """
        with self._lock:
            # 发送心跳
            success, response = OnlineAPI.report_heartbeat(self.client)
            self._last_heartbeat_time = time.time()
            self._last_heartbeat_success = success
            
            # 如果心跳成功，检查状态
            if success:
                uid = self.client.get_user_id()
                if uid:
                    self._last_status_check = OnlineAPI.is_online(self.client, uid)
                    if not self._last_status_check:
                        logger.warning(f"用户 {uid} 心跳状态检查失败，状态不是在线")
            else:
                logger.warning("心跳发送失败")
    
    def stop(self):
        """
        停止心跳线程
        """
        if self._is_running:
            logger.info("正在停止心跳线程...")
            self._stop_event.set()
            if threading.current_thread() != self:
                self.join(timeout=5)  # 等待线程结束，最多5秒
    
    def is_running(self):
        """
        检查心跳线程是否正在运行
        :return: 是否正在运行
        """
        return self._is_running
    
    def get_last_heartbeat_time(self):
        """
        获取最后一次心跳时间
        :return: 最后一次心跳时间（时间戳）
        """
        with self._lock:
            return self._last_heartbeat_time
    
    def get_last_heartbeat_status(self):
        """
        获取最后一次心跳状态
        :return: (心跳是否成功发送, 状态检查是否通过)
        """
        with self._lock:
            return self._last_heartbeat_success, self._last_status_check


# 全局心跳线程字典，用于管理所有心跳线程
# 键为客户端ID，值为HeartbeatThread实例
_heartbeat_threads = {}
_threads_lock = threading.RLock()


def start_heartbeat(client, interval=10):
    """
    启动心跳线程
    :param client: API客户端实例
    :param interval: 心跳间隔（秒），默认10秒
    :return: HeartbeatThread实例
    """
    client_id = id(client)
    
    with _threads_lock:
        # 检查是否已经存在心跳线程
        if client_id in _heartbeat_threads and _heartbeat_threads[client_id].is_running():
            logger.debug(f"客户端 {client_id} 的心跳线程已经在运行")
            return _heartbeat_threads[client_id]
        
        # 创建并启动新的心跳线程
        thread = HeartbeatThread(client, interval)
        thread.start()
        _heartbeat_threads[client_id] = thread
        logger.info(f"已启动客户端 {client_id} 的心跳线程")
        
        return thread


def stop_heartbeat(client):
    """
    停止心跳线程
    :param client: API客户端实例
    :return: 是否成功停止
    """
    client_id = id(client)
    
    with _threads_lock:
        if client_id in _heartbeat_threads:
            thread = _heartbeat_threads[client_id]
            thread.stop()
            del _heartbeat_threads[client_id]
            logger.info(f"已停止客户端 {client_id} 的心跳线程")
            return True
    
    return False


def stop_all_heartbeats():
    """
    停止所有心跳线程
    """
    with _threads_lock:
        for client_id, thread in list(_heartbeat_threads.items()):
            thread.stop()
            logger.info(f"已停止客户端 {client_id} 的心跳线程")
        
        _heartbeat_threads.clear()
        logger.info("已停止所有心跳线程") 