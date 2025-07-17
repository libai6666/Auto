docker build -t test-report-server .# 测试报告自动清理功能说明

本文档详细说明如何配置和使用测试报告的自动清理功能，以保持报告服务器的存储空间和性能。

## 自动清理功能

Docker 部署的报告服务器已配置为自动清理旧报告，默认清理策略如下：

- **清理频率**：每天凌晨 3 点执行清理
- **保留时间**：默认保留最近 30 天的报告
- **清理日志**：清理过程的日志保存在 `logs/report_cleaner.log` 文件中

## 配置清理策略

### 修改保留天数

您可以通过以下方式修改报告保留的天数：

1. **通过环境变量**：
   在 `docker-compose.yml` 文件中修改 `REPORT_RETENTION_DAYS` 环境变量：

   ```yaml
   environment:
     - REPORT_RETENTION_DAYS=60  # 修改为您需要的天数
   ```

2. **重新构建并启动容器**：
   ```bash
   docker-compose up -d --build report-server

   或者
      docker-compose build --no-cache=false report-server
   docker-compose up -d report-server  用缓存，会快一点
   ```
   docker logs test-report-server  --看看日志有没有启动

## 手动清理报告

除了自动清理外，您还可以随时手动清理旧报告：

### Windows 系统

1. 运行 `clean_old_reports.bat` 批处理文件
2. 输入要保留的天数（默认 30 天）
3. 确认操作

### Linux/Mac 系统

1. 运行 `clean_old_reports.sh` 脚本：
   ```bash
   chmod +x clean_old_reports.sh
   ./clean_old_reports.sh
   ```
2. 输入要保留的天数（默认 30 天）
3. 确认操作

### Docker 容器内手动清理

如果您需要在 Docker 容器内手动清理：

```bash
# 进入容器
docker exec -it test-report-server bash

# 运行清理脚本
python utils/notification/report_cleaner.py --days 30
```

## 清理脚本高级用法

清理脚本 `report_cleaner.py` 支持以下参数：

```
python utils/notification/report_cleaner.py [选项]

选项:
  --dir, -d DIR     报告根目录，默认为 "reports"
  --days, -D DAYS   报告保留天数，默认为 30
  --dry-run         仅模拟运行，不实际删除文件
```

### 示例

1. **模拟清理（不实际删除）**：
   ```bash
   python utils/notification/report_cleaner.py --dry-run
   ```

2. **清理 60 天前的报告**：
   ```bash
   python utils/notification/report_cleaner.py --days 60
   ```

3. **指定报告目录**：
   ```bash
   python utils/notification/report_cleaner.py --dir /path/to/reports --days 30
   ```

## 注意事项

- 清理操作是不可逆的，请确保设置合理的保留天数
- 建议定期检查清理日志，确保清理正常执行
- 如果您有特别重要的报告，建议手动备份 