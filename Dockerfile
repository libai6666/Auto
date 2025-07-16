FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 7987

# 设置容器启动命令
CMD ["python", "scripts/start_report_server.py", "--port", "7987"] 