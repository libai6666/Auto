FROM python:3.9-slim

WORKDIR /app

# 安装依赖和cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本文件
COPY scripts/start_report_server.py /app/scripts/
COPY utils /app/utils/
COPY config /app/config/

# 创建报告和日志目录
RUN mkdir -p /app/reports /app/logs

# 创建cron任务 - 每天凌晨3点运行清理脚本
COPY utils/notification/report_cleaner.py /app/utils/notification/
RUN echo "0 3 * * * cd /app && python /app/utils/notification/report_cleaner.py --dir /app/reports --days 30 >> /app/logs/report_cleaner.log 2>&1" > /etc/cron.d/report-cleaner && \
    chmod 0644 /etc/cron.d/report-cleaner && \
    crontab /etc/cron.d/report-cleaner

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 启动cron服务\n\
service cron start\n\
\n\
# 获取报告保留天数，默认为30天\n\
RETENTION_DAYS=${REPORT_RETENTION_DAYS:-30}\n\
\n\
# 更新cron任务中的保留天数\n\
sed -i "s/--days 30/--days $RETENTION_DAYS/g" /etc/cron.d/report-cleaner\n\
crontab /etc/cron.d/report-cleaner\n\
\n\
echo "已启动定时清理服务，每天凌晨3点清理${RETENTION_DAYS}天前的报告"\n\
\n\
# 设置环境变量告诉程序运行在Docker中\n\
export DOCKER_ENV=true\n\
\n\
# 显示目录结构，帮助调试\n\
echo "目录结构:"\n\
find /app -type f -name "*.py" | sort\n\
\n\
# 启动报告服务器\n\
cd /app && python /app/scripts/start_report_server.py --dir /app/reports --port 7987\n\
' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
EXPOSE 7987

# 设置容器启动命令
CMD ["/app/start.sh"] 