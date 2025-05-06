#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import subprocess
import pytest
import webbrowser
import re
import shutil
import yaml
from datetime import datetime, timedelta
from utils.logger import logger

# 默认配置
DEFAULT_REPORTS_RETENTION_DAYS = 30


def load_config():
    """
    加载配置文件
    :return: 配置字典
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.yaml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}


def cleanup_reports():
    """
    清理旧的报告文件
    根据配置保留最近N天的报告，删除更早的报告
    """
    # 加载配置
    config = load_config()
    cleanup_config = config.get('cleanup', {})
    
    # 检查是否启用清理
    if not cleanup_config.get('enabled', True):
        logger.info("文件自动清理功能已禁用")
        return
    
    # 获取保留天数
    retention_days = cleanup_config.get('reports_retention_days', DEFAULT_REPORTS_RETENTION_DAYS)
    
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return
    
    # 获取当前日期
    now = datetime.now()
    cutoff_date = now - timedelta(days=retention_days)
    
    logger.info(f"开始清理报告文件，保留最近{retention_days}天的报告...")
    
    # 用于匹配报告目录名称中的日期时间戳的正则表达式
    # 匹配格式如: html_report_20230526_120000, allure_results_20230526_120000
    pattern = r'(?:html_report|allure_results|allure_report)_(\d{8})_(\d{6})'
    
    removed_count = 0
    
    # 遍历reports目录下的所有子目录
    for item in os.listdir(reports_dir):
        item_path = os.path.join(reports_dir, item)
        
        # 如果是目录，检查是否是测试报告目录
        if os.path.isdir(item_path):
            match = re.search(pattern, item)
            if match:
                # 提取日期和时间
                date_str, time_str = match.groups()
                try:
                    # 解析日期和时间
                    item_datetime = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    
                    # 检查是否超过保留期限
                    if item_datetime < cutoff_date:
                        logger.debug(f"删除过期报告目录: {item_path}")
                        shutil.rmtree(item_path)
                        removed_count += 1
                except ValueError:
                    logger.warning(f"无法解析报告目录的日期时间: {item}")
    
    logger.info(f"报告清理完成，共删除了 {removed_count} 个过期报告目录")


def parse_args():
    """
    解析命令行参数
    :return: 解析结果
    """
    parser = argparse.ArgumentParser(description="接口测试自动化框架启动器")
    
    # 环境参数
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="test",
                        help="指定测试环境: dev, test 或 prod")
    
    # 测试用例参数
    parser.add_argument("--case", "-c", help="指定要运行的测试用例，支持模块/类/方法名")
    parser.add_argument("--module", "-m", help="指定要运行的测试模块")
    parser.add_argument("--marker", "-k", help="指定要运行的测试标记，如smoke, regression等")
    
    # 报告参数
    parser.add_argument("--report", action="store_true", help="是否生成HTML测试报告")
    parser.add_argument("--allure", action="store_true", help="是否生成Allure测试报告")
    parser.add_argument("--open", action="store_true", help="是否在浏览器中打开测试报告")
    
    # 执行参数
    parser.add_argument("--xdist", "-n", type=int, default=0,
                        help="并行执行测试的进程数，0表示不并行")
    parser.add_argument("--reruns", type=int, default=0,
                        help="失败重试次数，0表示不重试")
    
    # 调试参数
    parser.add_argument("--debug", action="store_true", help="是否开启调试模式")
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 设置工作目录为项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # 清理旧的报告文件
    cleanup_reports()
    
    # 日志记录
    logger.info("=" * 80)
    logger.info(f"启动接口自动化测试，时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"工作目录: {project_root}")
    logger.info(f"测试环境: {args.env}")
    
    # 准备测试命令参数
    pytest_args = ["-v"]
    
    # 添加环境参数
    pytest_args.extend(["--env", args.env])
    
    # 添加测试用例参数
    if args.case:
        pytest_args.append(args.case)
    
    if args.module:
        pytest_args.append(f"testcases/{args.module}")
    
    if args.marker:
        pytest_args.extend(["-m", args.marker])
    
    # 添加报告参数
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    if args.report:
        report_dir = f"reports/html_report_{timestamp}"
        os.makedirs(report_dir, exist_ok=True)
        pytest_args.extend(["--html", f"{report_dir}/report.html"])
    
    if args.allure:
        allure_results_dir = f"reports/allure_results_{timestamp}"
        os.makedirs(allure_results_dir, exist_ok=True)
        pytest_args.extend(["--alluredir", allure_results_dir])
    
    # 添加执行参数
    if args.xdist > 0:
        pytest_args.extend(["-n", str(args.xdist)])
    
    if args.reruns > 0:
        pytest_args.extend(["--reruns", str(args.reruns)])
    
    # 添加调试参数
    if args.debug:
        pytest_args.append("--verbose")
        os.environ["DEBUG_MODE"] = "1"
    
    # 记录测试命令
    logger.info(f"执行的Pytest参数: {' '.join(pytest_args)}")
    
    # 执行测试
    logger.info("开始执行测试...")
    exit_code = pytest.main(pytest_args)
    
    # 生成Allure报告（如果需要）
    if args.allure:
        logger.info("生成Allure报告...")
        allure_report_dir = f"reports/allure_report_{timestamp}"
        os.makedirs(allure_report_dir, exist_ok=True)
        
        # 设置Allure和JDK路径
        allure_bin = "D:\\tools\\allure-2.34.0\\bin\\allure.bat"
        
        # 确认文件存在
        if os.path.exists(allure_bin):
            logger.info(f"找到Allure可执行文件: {allure_bin}")
        else:
            logger.error(f"未找到Allure可执行文件: {allure_bin}")
            logger.info("请手动运行以下命令查看报告: allure serve reports/allure_results_*")
            return exit_code
        
        try:
            # 生成静态报告
            logger.info("正在生成Allure静态报告...")
            abs_results_dir = os.path.abspath(allure_results_dir)
            abs_report_dir = os.path.abspath(allure_report_dir)
            
            logger.info(f"执行命令: {allure_bin} generate {abs_results_dir} -o {abs_report_dir} --clean")
            subprocess.run([allure_bin, "generate", abs_results_dir, "-o", abs_report_dir, "--clean"],
                           check=True)
            logger.info(f"Allure静态报告已生成: {abs_report_dir}")
            
            # 打开报告
            if args.open:
                logger.info("在浏览器中打开Allure报告...")
                
                try:
                    # 使用Allure的完整路径来启动服务
                    logger.info(f"执行命令: {allure_bin} serve {abs_results_dir}")
                    
                    # 使用无窗口方式启动Allure服务
                    if sys.platform.startswith('win'):
                        # 创建无窗口进程的配置
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                        
                        # 直接运行allure serve命令，但不显示窗口
                        logger.info("以隐藏窗口方式启动Allure服务")
                        subprocess.Popen([allure_bin, "serve", abs_results_dir], 
                                        startupinfo=startupinfo,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=False)
                        logger.info("Allure服务已在后台启动，稍后将在浏览器中打开")
                        # 等待几秒钟，让服务有时间启动
                        time.sleep(2)
                        logger.info("报告应该已在浏览器中打开，如果没有自动打开，请访问 http://localhost:端口号")
                    else:
                        # 在Linux/Mac下使用不同的命令
                        subprocess.Popen([allure_bin, "serve", abs_results_dir], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE, 
                                         shell=False)
                        logger.info("Allure服务已启动")
                except Exception as e:
                    logger.error(f"启动Allure服务出错: {str(e)}")
                    logger.info(f"您可以手动执行以下命令查看报告: {allure_bin} serve {abs_results_dir}")
        except subprocess.CalledProcessError as e:
            logger.error(f"生成Allure报告失败: {str(e)}")
            logger.error(f"请确保已安装Allure命令行工具并设置正确的路径: {allure_bin}")
        except Exception as e:
            logger.error(f"处理Allure报告时出错: {str(e)}")
            logger.info(f"您可以手动执行以下命令查看报告: {allure_bin} serve {abs_results_dir}")
    
    # 打开HTML报告（如果需要）
    elif args.report and args.open:
        report_path = f"{report_dir}/report.html"
        if os.path.exists(report_path):
            logger.info("在浏览器中打开HTML报告...")
            webbrowser.open_new_tab(f"file://{os.path.abspath(report_path)}")
    
    # 输出测试结果
    logger.info("=" * 80)
    logger.info(f"测试执行完成，退出码: {exit_code}")
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 