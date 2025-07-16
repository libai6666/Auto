# config.yaml配置详解

本文档详细解释配置文件`config/config.yaml`中16-34行的配置项，包括它们的含义、用途和在代码中的实际应用位置。

## 配置概览

`config.yaml`的16-34行包含以下三个主要部分：

```yaml
# 请求配置
request:
  headers:
    Content-Type: "application/json"
    User-Agent: "DuooInterfaceAuto/1.0"
  verify_ssl: false
  max_retries: 3
  retry_delay: 1

# 测试控制
test_control:
  screenshot_on_failure: true
  allow_rerun_failed: true
  max_rerun_times: 2
  generate_report: true

# 其他配置
email_notify: false
debug_mode: true
```

## 配置详解

### 1. 请求配置 (request)

这部分配置控制HTTP请求的行为，包括默认请求头、SSL验证和重试策略。

#### 1.1 headers

```yaml
headers:
  Content-Type: "application/json"
  User-Agent: "DuooInterfaceAuto/1.0"
```

- **作用**：设置所有HTTP请求的默认请求头
- **使用位置**：
  - `utils/api_client.py`中的`__init__`方法：
  ```python
  # 设置请求头
  default_headers = config.get("request", {}).get("headers", {})
  self.session.headers.update(default_headers)
  ```
- **影响范围**：
  - `Content-Type: "application/json"`告诉服务器请求体是JSON格式
  - `User-Agent: "DuooInterfaceAuto/1.0"`标识请求来源是自动化测试框架

#### 1.2 verify_ssl

```yaml
verify_ssl: false
```

- **作用**：控制是否验证SSL证书
- **使用位置**：
  - `utils/api_client.py`中的`__init__`方法：
  ```python
  # 设置是否验证SSL
  self.verify_ssl = config.get("request", {}).get("verify_ssl", True)
  ```
  - `utils/api_client.py`中的`request`方法：
  ```python
  response = self.session.request(
      method=method,
      url=url,
      params=params,
      data=data,
      json=json,
      headers=headers,
      files=files,
      timeout=self.timeout,
      verify=self.verify_ssl,  # 使用配置的verify_ssl
      **kwargs
  )
  ```
- **影响范围**：
  - `false`：不验证SSL证书，适用于测试环境或自签名证书
  - `true`：验证SSL证书，适用于生产环境

#### 1.3 max_retries

```yaml
max_retries: 3
```

- **作用**：设置请求失败时的最大重试次数
- **使用位置**：
  - `utils/api_client.py`中的`__init__`方法：
  ```python
  # 重试配置
  retry_config = config.get("request", {})
  retries = retry_config.get("max_retries", 3)
  
  # 设置重试策略
  retry_strategy = Retry(
      total=retries,
      backoff_factor=retry_delay,
      status_forcelist=[429, 500, 502, 503, 504],
      allowed_methods=["HEAD", "GET", "PUT", "POST", "DELETE", "OPTIONS", "TRACE"]
  )
  ```
- **影响范围**：
  - 当请求遇到特定错误（如服务器错误500、502等）时自动重试
  - 提高测试稳定性，处理临时网络问题或服务器波动

#### 1.4 retry_delay

```yaml
retry_delay: 1
```

- **作用**：设置重试之间的延迟时间（秒）
- **使用位置**：
  - `utils/api_client.py`中与`max_retries`一起使用：
  ```python
  retry_delay = retry_config.get("retry_delay", 1)
  
  # 设置重试策略
  retry_strategy = Retry(
      total=retries,
      backoff_factor=retry_delay,  # 使用配置的重试延迟
      # ...
  )
  ```
- **影响范围**：
  - 控制重试间隔，避免立即重试对服务器造成压力
  - 当`backoff_factor=1`时，重试间隔为[1s, 2s, 4s, ...]

### 2. 测试控制 (test_control)

这部分配置控制测试执行过程中的行为。

#### 2.1 screenshot_on_failure

```yaml
screenshot_on_failure: true
```

- **作用**：控制测试失败时是否截图（用于UI测试或API响应保存）
- **使用位置**：
  - `testcases/conftest.py`中的`pytest_runtest_makereport`钩子：
  ```python
  @pytest.hookimpl(tryfirst=True, hookwrapper=True)
  def pytest_runtest_makereport(item, call):
      # ...
      if report.when == "call" and report.failed:
          # 从配置中获取是否截图
          config = load_config()
          if config.get("test_control", {}).get("screenshot_on_failure", False):
              # 添加失败信息
              allure.attach(
                  response.text,
                  name="响应内容",
                  attachment_type=allure.attachment_type.TEXT
              )
  ```
- **影响范围**：
  - 当测试失败时，自动保存API响应内容到测试报告
  - 有助于调试和分析失败原因

#### 2.2 allow_rerun_failed

```yaml
allow_rerun_failed: true
```

- **作用**：控制是否允许重新运行失败的测试用例
- **使用位置**：
  - `run.py`中的主函数：
  ```python
  # 添加执行参数
  if args.reruns <= 0:  # 如果命令行未指定
      config = load_config()
      test_control = config.get("test_control", {})
      if test_control.get("allow_rerun_failed", False):
          reruns = test_control.get("max_rerun_times", 0)
          pytest_args.extend(["--reruns", str(reruns)])
  ```
- **影响范围**：
  - 当测试用例失败时，自动重新运行
  - 减少由于临时性问题导致的测试失败

#### 2.3 max_rerun_times

```yaml
max_rerun_times: 2
```

- **作用**：设置失败测试用例最大重新运行次数
- **使用位置**：
  - 与`allow_rerun_failed`在`run.py`中一起使用：
  ```python
  if test_control.get("allow_rerun_failed", False):
      reruns = test_control.get("max_rerun_times", 0)
      pytest_args.extend(["--reruns", str(reruns)])
  ```
- **影响范围**：
  - 控制单个失败测试用例最多重试的次数
  - 避免无限重试，防止测试执行时间过长

#### 2.4 generate_report

```yaml
generate_report: true
```

- **作用**：控制是否自动生成测试报告
- **使用位置**：
  - `run.py`中的主函数：
  ```python
  # 判断是否需要自动生成报告
  config = load_config()
  if config.get("test_control", {}).get("generate_report", False) and not (args.report or args.allure):
      # 自动添加HTML报告参数
      report_dir = f"reports/html_report_{timestamp}"
      os.makedirs(report_dir, exist_ok=True)
      pytest_args.extend(["--html", f"{report_dir}/report.html"])
  ```
- **影响范围**：
  - 即使没有指定命令行参数，也会生成报告
  - 确保每次测试都有结果记录

### 3. 其他配置

#### 3.1 email_notify

```yaml
email_notify: false
```

- **作用**：控制测试完成后是否发送邮件通知
- **使用位置**：
  - `run.py`中测试完成后的处理：
  ```python
  # 测试完成后发送邮件通知
  config = load_config()
  if config.get("email_notify", False):
      from utils.email_utils import send_report_email
      logger.info("正在发送邮件通知...")
      send_report_email(exit_code, report_path)
  ```
- **影响范围**：
  - `true`：测试完成后自动发送邮件（需要`email_config.yaml`中配置邮件服务器）
  - `false`：不发送邮件通知

#### 3.2 debug_mode

```yaml
debug_mode: true
```

- **作用**：控制是否启用调试模式
- **使用位置**：
  - `utils/logger.py`中的日志级别设置：
  ```python
  def setup_logger():
      config = load_config()
      debug_mode = config.get("debug_mode", False)
      
      # 设置日志级别
      log_level = "DEBUG" if debug_mode else "INFO"
      logger.remove()  # 移除默认处理器
      logger.add(sys.stderr, level=log_level)
      # ...
  ```
  - 在多处代码中控制详细日志输出：
  ```python
  if config.get("debug_mode", False):
      logger.debug(f"详细请求信息: {json.dumps(request_data, indent=2)}")
  ```
- **影响范围**：
  - `true`：启用详细日志记录，包括请求和响应的完整内容
  - `false`：仅记录基本信息，减少日志体积

## 配置修改示例

### 场景1: 提高接口测试稳定性

```yaml
request:
  headers:
    Content-Type: "application/json"
    User-Agent: "DuooInterfaceAuto/1.0"
  verify_ssl: false
  max_retries: 5    # 增加重试次数
  retry_delay: 2    # 增加重试延迟

test_control:
  screenshot_on_failure: true
  allow_rerun_failed: true
  max_rerun_times: 3    # 增加失败用例重试次数
  generate_report: true

debug_mode: false    # 关闭调试模式，减少日志量
```

### 场景2: 开发调试环境

```yaml
request:
  headers:
    Content-Type: "application/json"
    User-Agent: "DuooInterfaceAuto/1.0"
  verify_ssl: false
  max_retries: 0    # 禁用重试，立即查看失败
  retry_delay: 0

test_control:
  screenshot_on_failure: true
  allow_rerun_failed: false    # 禁用失败重试
  max_rerun_times: 0
  generate_report: true

debug_mode: true    # 启用调试模式，查看详细日志
```

### 场景3: 生产环境测试

```yaml
request:
  headers:
    Content-Type: "application/json"
    User-Agent: "DuooInterfaceAuto/Production/1.0"
  verify_ssl: true    # 启用SSL验证
  max_retries: 2
  retry_delay: 1

test_control:
  screenshot_on_failure: true
  allow_rerun_failed: true
  max_rerun_times: 1
  generate_report: true

email_notify: true    # 启用邮件通知
debug_mode: false
```

## 最佳实践

1. **环境隔离**：为不同环境（开发、测试、生产）创建不同的配置文件或配置节
2. **性能平衡**：在稳定性和执行效率之间找到平衡点
3. **安全性考虑**：生产环境应启用SSL验证，非生产环境可禁用以便调试
4. **灵活重试**：为不稳定的服务设置适当的重试策略
5. **有效日志**：根据需要开启debug_mode，避免日志过于冗长 