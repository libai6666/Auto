#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通知模块
包含各种通知方式的实现
"""

from utils.notification.dingtalk import DingTalkSender, get_default_dingtalk_sender
from utils.notification.report_server import start_report_server, add_report, stop_report_server, get_report_server 