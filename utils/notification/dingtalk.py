#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
import base64
import hmac
import hashlib
import urllib.parse
import requests
from datetime import datetime
from utils.logger import logger


class DingTalkSender:
    """
    钉钉机器人消息发送工具
    用于将测试报告发送到钉钉群
    """

    def __init__(self, webhook_url=None, secret=None):
        """
        初始化钉钉机器人
        :param webhook_url: 钉钉机器人的Webhook地址
        :param secret: 钉钉机器人的签名密钥
        """
        self.webhook_url = webhook_url
        self.secret = secret

    def _get_signed_url(self):
        """
        生成带签名的URL
        :return: 带签名的URL
        """
        if not self.secret:
            return self.webhook_url
        
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            key=self.secret.encode(), 
            msg=string_to_sign.encode(), 
            digestmod=hashlib.sha256
        ).digest()
        
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    def send_text(self, content, at_mobiles=None, at_all=False):
        """
        发送文本消息
        :param content: 消息内容
        :param at_mobiles: @的手机号列表
        :param at_all: 是否@所有人
        :return: 请求响应
        """
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles if at_mobiles else [],
                "isAtAll": at_all
            }
        }
        
        return self._send_message(data)

    def send_markdown(self, title, text, at_mobiles=None, at_all=False):
        """
        发送markdown消息
        :param title: 消息标题
        :param text: markdown格式的消息内容
        :param at_mobiles: @的手机号列表
        :param at_all: 是否@所有人
        :return: 请求响应
        """
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles if at_mobiles else [],
                "isAtAll": at_all
            }
        }
        
        return self._send_message(data)

    def send_link(self, title, text, message_url, pic_url=""):
        """
        发送链接消息
        :param title: 消息标题
        :param text: 消息内容
        :param message_url: 点击消息跳转的URL
        :param pic_url: 图片URL
        :return: 请求响应
        """
        data = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "picUrl": pic_url,
                "messageUrl": message_url
            }
        }
        
        return self._send_message(data)

    def _send_message(self, data):
        """
        发送消息到钉钉
        :param data: 消息数据
        :return: 请求响应
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        url = self._get_signed_url()
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            logger.info(f"钉钉消息发送状态: {response.status_code}")
            logger.debug(f"钉钉响应内容: {response.text}")
            return response
        except Exception as e:
            logger.error(f"发送钉钉消息失败: {str(e)}")
            return None

    def send_test_report(self, report_info):
        """
        发送测试报告摘要
        :param report_info: 测试报告信息字典，包含以下字段:
            - total: 总用例数
            - passed: 通过用例数
            - failed: 失败用例数
            - skipped: 跳过用例数
            - error: 错误用例数
            - duration: 测试持续时间(秒)
            - report_url: 报告URL(可选)
            - env: 测试环境
        :return: 请求响应
        """
        # 计算通过率
        total = report_info.get('total', 0)
        passed = report_info.get('passed', 0)
        pass_rate = f"{(passed / total * 100):.2f}%" if total > 0 else "0.00%"
        
        # 格式化持续时间
        duration = report_info.get('duration', 0)
        duration_str = f"{duration // 60}分{duration % 60}秒" if duration >= 60 else f"{duration}秒"
        
        # 获取当前时间
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建Markdown消息
        title = f"自动化测试报告 - {report_info.get('env', '未知环境')}"
        
        text = f"### 自动化测试报告摘要 \n\n"
        text += f"**测试环境**: {report_info.get('env', '未知环境')} \n\n"
        text += f"**执行时间**: {now} \n\n"
        text += f"**测试结果**: \n\n"
        text += f"- 总用例数: {total} \n"
        text += f"- 通过用例: {passed} \n"
        text += f"- 失败用例: {report_info.get('failed', 0)} \n"
        text += f"- 跳过用例: {report_info.get('skipped', 0)} \n"
        text += f"- 错误用例: {report_info.get('error', 0)} \n"
        text += f"- 通过率: {pass_rate} \n"
        text += f"- 执行时间: {duration_str} \n\n"
        
        # 如果有报告URL，添加链接
        if 'report_url' in report_info and report_info['report_url']:
            text += f"[查看详细报告]({report_info['report_url']}) \n\n"
        
        # 根据通过率添加不同的结论
        if passed == total:
            text += "✅ **测试全部通过!** "
        elif passed / total >= 0.9:
            text += "⚠️ **大部分测试通过，请检查失败项** "
        else:
            text += "❌ **测试存在较多失败，请及时处理!** "
        
        # 发送markdown消息
        return self.send_markdown(title, text)


def get_default_dingtalk_sender():
    """
    获取默认的钉钉发送器
    :return: DingTalkSender实例
    """
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=488a1909c0d0e876a8f32ccc1a6c783cd098c9105c2e268049d074492d0d0887"
    secret = "SECe3acba11819fe56d2639e1ba4797bf700be59eb0039a969add8e5c375ccb0946"
    return DingTalkSender(webhook_url, secret)


if __name__ == "__main__":
    # 测试代码
    sender = get_default_dingtalk_sender()
    
    # 测试发送文本消息
    sender.send_text("这是一条测试消息，来自自动化测试框架")
    
    # 测试发送测试报告
    test_report = {
        "total": 100,
        "passed": 95,
        "failed": 3,
        "skipped": 1,
        "error": 1,
        "duration": 125,
        "env": "测试环境",
        "report_url": "http://example.com/report"
    }
    sender.send_test_report(test_report) 