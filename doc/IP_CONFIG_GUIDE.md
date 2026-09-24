# 报告服务器IP地址配置指南

## 问题说明

之前的配置中硬编码了固定的IP地址：
- `docker-compose.yml` 中设置了 `REPORT_SERVER_HOST=192.168.0.105`
- `config.yaml` 中设置了 `url: "http://192.168.0.110:7987"`

当公司局域网IP地址变更时，这些配置会失效，导致报告链接无法访问。

## 解决方案

### 1. 自动检测IP地址（推荐）✅

**已修改的配置和代码：**

#### docker-compose.yml
```yaml
environment:
  - DOCKER_ENV=true
  # 留空将自动检测当前局域网IP地址
  # - REPORT_SERVER_HOST=192.168.0.105
  - REPORT_RETENTION_DAYS=30
```

注释掉 `REPORT_SERVER_HOST` 后，系统会自动检测当前机器的局域网IP地址。

#### config.yaml
```yaml
report_server:
  url: "http://localhost:7987"  # 会自动替换为局域网IP
  enabled: true
```

使用 `localhost` 作为默认配置，**但在生成报告URL时会自动替换为局域网IP**。

#### 新增工具模块：utils/network_utils.py
提供自动检测局域网IP的功能：
- 优先从环境变量 `REPORT_SERVER_HOST` 获取
- 自动通过网络连接检测本机局域网IP
- 降级方案：使用hostname获取IP

#### 修改报告服务器模块：utils/notification/report_server.py
`add_report` 函数增强：
- 自动检测配置中的 `localhost` 并替换为实际局域网IP
- 确保钉钉通知中的报告链接使用局域网IP而非localhost

### 2. 工作原理

#### Docker容器启动时（报告服务器）
按以下顺序获取IP地址：

1. **环境变量优先**：如果设置了 `REPORT_SERVER_HOST` 环境变量，使用该值
2. **自动检测**：通过连接外部DNS服务器（8.8.8.8）获取本机的局域网IP
3. **回退方案**：使用 `socket.gethostbyname(socket.gethostname())` 获取主机名对应的IP

#### 生成报告URL时（钉钉通知）
当配置文件中使用 `localhost` 时：

1. **检测localhost**：`add_report` 函数检测到配置URL包含 `localhost`
2. **自动替换**：调用 `get_report_server_url()` 获取真实的局域网IP
3. **生成URL**：使用局域网IP生成最终的报告链接
4. **发送通知**：钉钉通知中的链接为 `http://192.168.x.x:7987/report_xxx`

**举例说明：**
- 配置文件：`http://localhost:7987`
- 实际生成：`http://192.168.0.105:7987/report_20251021_105403`
- 钉钉显示：局域网内所有人都能访问 ✅

### 3. 使用场景

#### 场景A：IP地址频繁变更（当前场景）
**解决方法：** 保持 `REPORT_SERVER_HOST` 注释状态（已配置）

每次启动Docker容器时，系统会自动检测当前的IP地址，无需手动修改配置。

#### 场景B：有固定IP或域名
如果您的服务器有固定IP或域名，可以取消注释并设置：

```yaml
environment:
  - DOCKER_ENV=true
  - REPORT_SERVER_HOST=your-fixed-ip-or-domain.com
  - REPORT_RETENTION_DAYS=30
```

#### 场景C：临时指定IP地址
在启动Docker时通过命令行指定：

```bash
# Linux/Mac
REPORT_SERVER_HOST=192.168.1.100 docker-compose up -d

# Windows PowerShell
$env:REPORT_SERVER_HOST="192.168.1.100"; docker-compose up -d

# Windows CMD
set REPORT_SERVER_HOST=192.168.1.100 && docker-compose up -d
```

### 4. 重新部署

**本次修改内容：**
- ✅ 新增了代码文件 `utils/network_utils.py`
- ✅ 修改了代码文件 `utils/notification/report_server.py`
- ✅ 修改了配置文件 `docker-compose.yml` 和 `config.yaml`

**因为修改了Python代码，需要重新构建Docker镜像：**

```bash
# 停止现有容器
docker-compose down

# 重新构建并启动
docker-compose up --build -d

# 查看日志确认启动成功
docker logs test-report-server
```

**预期日志输出：**
```
自动检测到局域网IP: 192.168.0.xxx
报告服务器已启动: http://192.168.0.xxx:7987
报告可通过以下URL访问：
- 本机访问: http://localhost:7987
- 服务器访问: http://192.168.0.xxx:7987
```

### 5. 验证配置

#### 步骤1：检查Docker报告服务器
启动后，查看日志确认使用的IP地址：

```bash
docker logs test-report-server
```

日志中会显示类似以下内容：
```
自动检测到局域网IP: 192.168.0.xxx
报告可通过以下URL访问：
- 本机访问: http://localhost:7987
- 服务器访问: http://192.168.0.xxx:7987
- 注意: 在Docker环境中运行，请使用宿主机IP访问
```

#### 步骤2：运行测试并发送钉钉通知
```bash
# 运行测试，生成Allure报告，并发送钉钉通知
python run.py --allure --dingtalk
```

#### 步骤3：检查钉钉通知中的链接
查看钉钉群消息，点击"查看详细报告"链接，应该显示为：
```
http://192.168.0.xxx:7987/report_20251021_105403/index.html
```

**而不是：**
```
http://localhost:7987/report_20251021_105403/index.html  ❌
```

#### 步骤4：确认链接可访问
局域网内其他同事点击钉钉中的链接，应该能够正常访问报告页面。✅

### 6. 访问报告

启动后，可以通过以下方式访问：

- **本机访问**：http://localhost:7987
- **局域网访问**：http://[当前IP]:7987（从日志中查看实际IP）
- **报告列表**：访问根URL可以看到所有测试报告的列表

### 7. 常见问题

**Q1: 为什么端口映射不需要改成 `0.0.0.0:7987:7987`？**

A: Docker的端口映射格式是 `宿主机端口:容器端口`，例如 `7987:7987`。
   - `7987:7987` 表示将容器的7987端口映射到宿主机的7987端口
   - Docker默认会监听所有网络接口（相当于0.0.0.0）
   - `0.0.0.0:7987:7987` 是错误的格式

**Q2: 钉钉通知中的链接还是localhost怎么办？**

A: 检查以下几点：
   1. 确保已重新构建Docker镜像：`docker-compose up --build -d`
   2. 确保 `utils/network_utils.py` 文件已正确复制到容器中
   3. 查看测试运行时的日志，确认是否输出：`将localhost替换为局域网IP: http://192.168.x.x:7987`
   4. 如果问题仍存在，手动在配置中指定IP：
      ```yaml
      report_server:
        url: "http://192.168.0.105:7987"  # 替换为实际IP
      ```

**Q3: 自动检测的IP地址不对怎么办？**

A: 可以在 `docker-compose.yml` 中手动指定：
```yaml
environment:
  - REPORT_SERVER_HOST=192.168.0.105  # 取消注释并设置正确的IP
```

**Q4: 如何确认自动IP替换功能是否生效？**

A: 运行测试时查看日志输出：
```bash
python run.py --allure --dingtalk

# 日志中应该包含：
# [INFO] 将localhost替换为局域网IP: http://192.168.0.xxx:7987
# [INFO] 报告已准备就绪，可通过以下URL访问: http://192.168.0.xxx:7987/report_xxx
```

**Q5: Docker容器和运行测试的机器不在同一台怎么办？**

A: 如果Docker部署在服务器A，但在机器B上运行测试：
   1. 在机器B的 `config.yaml` 中配置服务器A的IP：
      ```yaml
      report_server:
        url: "http://服务器A的IP:7987"
      ```
   2. 确保网络可达且端口7987已开放

## 总结

### ✅ 推荐配置（适用于IP频繁变更的场景）

**配置保持：**
- `docker-compose.yml`：`REPORT_SERVER_HOST` 注释状态
- `config.yaml`：`url: "http://localhost:7987"`

**自动化特性：**
1. **Docker报告服务器**：每次启动自动检测当前局域网IP
2. **钉钉通知链接**：自动将localhost替换为实际局域网IP
3. **IP变更无感知**：IP改变后，只需重启Docker容器即可

**工作流程：**
```
配置文件使用localhost
         ↓
运行测试时自动检测IP
         ↓
生成局域网IP的报告链接
         ↓
钉钉通知中显示真实IP
         ↓
团队成员都能访问 ✅
```

### ✅ 固定IP配置（适用于有固定IP的场景）

**配置修改：**
- `docker-compose.yml`：取消 `REPORT_SERVER_HOST` 注释并设置固定IP
- 或 `config.yaml`：直接设置固定IP的URL

**适用场景：**
- 服务器有固定IP地址
- 服务器有域名
- 不希望每次都自动检测IP

**优势：**
- 一次配置，长期使用
- 不依赖自动检测机制

