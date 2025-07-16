@echo off
setlocal enabledelayedexpansion
echo 启动测试报告Docker服务器...

REM 检查docker是否安装
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: docker未安装，请先安装docker和docker-compose
    exit /b 1
)

REM 检查docker-compose是否安装
where docker-compose >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: docker-compose未安装，请先安装docker-compose
    exit /b 1
)

REM 构建并启动容器
echo 构建并启动Docker容器...
docker-compose up -d --build

REM 等待容器启动
echo 等待服务启动...
timeout /t 5 /nobreak > nul

REM 获取容器状态
FOR /F "tokens=* USEBACKQ" %%F IN (`docker ps -f name^=test-report-server --format "{{.Status}}"`) DO (
    SET CONTAINER_STATUS=%%F
)

echo 容器状态: %CONTAINER_STATUS%

REM 检查容器是否运行
echo %CONTAINER_STATUS% | findstr /C:"Up" > nul
if %ERRORLEVEL% equ 0 (
    echo 测试报告服务器已成功启动!
    
    REM 获取本机IP地址
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
        set HOST_IP=%%a
        set HOST_IP=!HOST_IP:~1!
        goto :found_ip
    )
    
    :found_ip
    echo 您可以通过以下地址访问测试报告:
    echo http://%HOST_IP%:7987
    
    echo 容器日志:
    docker logs test-report-server
) else (
    echo 错误: 容器启动失败，请检查日志:
    docker logs test-report-server
    exit /b 1
)

echo 按任意键退出...
pause > nul 