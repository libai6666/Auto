# Docker 版测试报告服务部署指南

本文档详细说明如何将测试报告服务部署到 Docker 中，并配置为开机自启动。
 改动配置后重新部署docker方法：
 
```bash
 docker-compose up --build -d
 
```
 

## 前置条件

- Docker 已安装（Docker Desktop 或 Docker Engine）
- Docker Compose 已安装
- 对于 Linux：需要 root 权限安装系统服务（如需系统级自启动）
- 对于 Windows：需要管理员权限设置开机自启（如需系统级自启动）

> **注意**：如果您使用 Docker Desktop，它通常会在系统启动时自动运行。在 Docker Desktop 设置中可以配置"Start Docker Desktop when you log in"选项来控制Docker Desktop是否随系统启动。

## Docker 容器自启动说明

在我们的 `docker-compose.yml` 配置文件中，已经设置了 `restart: always` 策略，这意味着：

1. 容器会在退出时自动重启
2. 当 Docker 守护进程启动时（如系统重启后），容器会自动启动
3. 这不需要任何额外的系统级自启动脚本

对于不同系统类型的自启动处理：

- **使用 Docker Desktop (Windows/Mac)**：
  - 确保 Docker Desktop 设置为随系统启动
  - 容器会随 Docker Desktop 自动启动
  - **无需**执行额外的自启动脚本

- **使用 Docker Engine (Linux)**：
  - Docker 服务一般配置为系统启动时自动运行
  - 容器会随 Docker 服务自动启动
  - **可选**配置系统服务确保 Docker 自身自启动

因此，在大多数情况下，您只需部署容器，系统重启后容器会自动运行，不需要额外的自启动配置。

## 部署方法

### 方法一：使用脚本部署（推荐）

#### 第一步：克隆项目代码

确保您已经获取了完整的项目代码。

#### 第二步：启动 Docker 容器

##### Linux 系统

```bash
# 给脚本添加执行权限
chmod +x start_docker_report_server.sh

# 运行启动脚本
./start_docker_report_server.sh
```

##### Windows 系统

双击运行 `start_docker_report_server.bat` 文件。

### 方法二：手动命令部署

如果您希望使用命令行手动部署，可以按照以下步骤操作：

```bash
# 1. 确保您位于项目根目录（包含docker-compose.yml的目录）
cd /path/to/DuooInterfaceAuto

# 2. 构建Docker镜像
docker build -t test-report-server .

# 3. 启动服务
docker-compose up -d

# 4. 查看服务状态
docker ps | grep test-report-server

# 5. 查看服务日志
docker logs test-report-server
```

启动后，可通过 `http://localhost:7987` 或 `http://[服务器IP]:7987` 访问报告。

### 第三步：配置开机自启（可选）

> **注意**：如果使用 Docker Desktop，可以在 Docker Desktop 设置中勾选"Start Docker Desktop when you log in"，并在容器配置中设置`restart: always`（我们的docker-compose.yml已设置），这样系统启动后 Docker Desktop 会自动运行并启动标记为 always 的容器，无需额外配置系统级自启动。

#### Linux 系统

```bash
# 给安装脚本添加执行权限
chmod +x install_docker_service.sh

# 以 root 权限运行安装脚本
sudo ./install_docker_service.sh
```

#### Windows 系统

以管理员身份运行 `install_windows_service.bat` 文件。

## 访问测试报告

启动服务后，可以通过以下地址访问测试报告：

- 本机访问：http://localhost:7987
- 局域网访问：http://[服务器IP]:7987

## 管理服务

### Docker 容器管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker logs test-report-server

```

### 系统服务管理（Linux）

```bash
# 启动服务
sudo systemctl start report-server.service

# 停止服务
sudo systemctl stop report-server.service

# 查看状态
sudo systemctl status report-server.service

# 查看日志
sudo journalctl -u report-server.service
```

## 自定义配置

### 修改端口

如果需要修改默认端口 (7987)，请同时更新以下文件：

1. `docker-compose.yml` 文件中的端口映射
2. `Dockerfile` 中的 `EXPOSE` 指令

### 设置固定域名或IP

如果您有固定的公网 IP 或域名，可以在 `docker-compose.yml` 文件中设置环境变量：

```yaml
environment:
  - DOCKER_ENV=true
  - REPORT_SERVER_HOST=your-domain.com  # 替换为您的域名
```

## 故障排除

1. **容器无法启动**
   
   查看 Docker 日志：
   ```bash
   docker logs test-report-server
   ```

2. **无法访问服务**
   
   - 确认防火墙是否开放了 7987 端口
   - 检查容器是否正常运行：`docker ps | grep test-report-server`
   - 尝试在服务器上访问：`curl http://localhost:7987`

3. **开机自启动失败**
   
   - Linux：检查系统服务状态 `systemctl status report-server.service`
   - Windows：检查启动文件夹中的快捷方式是否正确

## 注意事项

- 数据持久化：所有报告数据存储在 `./reports` 目录，确保该目录有足够的磁盘空间
- 日志文件：所有日志文件存储在 `./logs` 目录
- 安全性：默认配置下，报告服务器在局域网内可访问，如需公网访问请考虑配置 HTTPS 和访问控制 