# 通知模块

本模块提供各种通知方式的实现，用于发送测试报告和其他通知。

## 钉钉通知工具 (dingtalk.py)

该工具用于将测试报告发送到钉钉群，方便团队成员及时了解测试结果。

### 使用方法

在运行测试时添加 `--dingtalk` 参数即可自动发送测试报告到钉钉群：

```bash
python run.py --allure --dingtalk
```

### 配置说明

钉钉机器人的配置信息在 `dingtalk.py` 的 `get_default_dingtalk_sender` 函数中设置：

```python
def get_default_dingtalk_sender():
    """
    获取默认的钉钉发送器
    :return: DingTalkSender实例
    """
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=你的access_token"
    secret = "你的签名密钥"
    return DingTalkSender(webhook_url, secret)
```

如需修改钉钉机器人配置，请直接编辑上述函数中的 `webhook_url` 和 `secret` 值。

### 支持的消息类型

1. **文本消息**：`send_text(content, at_mobiles=None, at_all=False)`
2. **Markdown消息**：`send_markdown(title, text, at_mobiles=None, at_all=False)`
3. **链接消息**：`send_link(title, text, message_url, pic_url="")`
4. **测试报告摘要**：`send_test_report(report_info)`

### 测试报告格式

测试报告以Markdown格式发送，包含以下信息：

- 测试环境
- 执行时间
- 测试结果统计（总数、通过数、失败数、跳过数、错误数）
- 通过率
- 执行时间
- 报告链接（如果有）
- 测试结果评估

### 单独使用

您也可以在其他脚本中单独使用该工具：

```python
from utils.notification.dingtalk import DingTalkSender

# 创建发送器实例
sender = DingTalkSender(webhook_url, secret)

# 发送文本消息
sender.send_text("测试完成")

# 发送测试报告
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
``` 