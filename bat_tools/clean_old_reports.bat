@echo off
setlocal enabledelayedexpansion

echo 测试报告清理工具
echo =====================================

set /p DAYS="请输入要保留的天数 (默认30天): "
if "!DAYS!"=="" set DAYS=30

echo.
echo 将清理 !DAYS! 天前的报告
echo.
set /p CONFIRM="是否继续? (Y/N): "

if /i "!CONFIRM!"=="Y" (
    echo.
    echo 正在清理报告...
    python utils/notification/report_cleaner.py --days !DAYS!
    echo.
    echo 清理完成!
) else (
    echo.
    echo 操作已取消
)

pause 