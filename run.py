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


def clear_today_logs():
    """
    清空当天的日志内容
    用于debug模式下，每次执行前清空日志，方便排查问题
    """
    # 获取当前日期的日志文件路径
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    today_log_file = os.path.join(log_dir, datetime.now().strftime("%Y-%m-%d") + ".log")
    
    # 检查文件是否存在
    if os.path.exists(today_log_file):
        try:
            # 清空文件内容（打开文件并立即关闭，使用'w'模式会清空文件）
            with open(today_log_file, 'w', encoding='utf-8') as f:
                pass
            logger.info("已清空当天日志文件，进入调试模式")
        except Exception as e:
            logger.error(f"清空当天日志文件失败: {str(e)}")
    else:
        # 如果文件不存在，创建一个空文件
        try:
            os.makedirs(os.path.dirname(today_log_file), exist_ok=True)
            with open(today_log_file, 'w', encoding='utf-8') as f:
                pass
            logger.info("已创建新的日志文件，进入调试模式")
        except Exception as e:
            logger.error(f"创建日志文件失败: {str(e)}")


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
    parser.add_argument("--debug", action="store_true", help="是否开启调试模式，开启后会清空当天日志内容")
    
    # 钉钉通知参数
    parser.add_argument("--dingtalk", action="store_true", help="是否发送测试报告到钉钉群")
    
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
    
    # 如果开启了debug模式，清空当天日志
    if args.debug:
        clear_today_logs()
    
    # 清理旧的报告文件
    # cleanup_reports()
    
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
        logger.info("已启用调试模式")
    
    # 记录测试命令
    logger.info(f"执行的Pytest参数: {' '.join(pytest_args)}")
    
    # 记录测试开始时间
    start_time = time.time()
    
    # 执行测试
    logger.info("开始执行测试...")
    exit_code = pytest.main(pytest_args)
    
    # 计算测试持续时间
    duration = int(time.time() - start_time)
    
    # 生成Allure报告（如果需要）
    allure_report_url = None
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
            
            # 设置默认报告URL（用于钉钉通知）
            allure_report_url = f"file:///{abs_report_dir}/index.html"
            
            # 启动报告服务器并添加报告
            if args.dingtalk:
                try:
                    from utils.notification import add_report
                    
                    logger.info("将报告上传到报告服务...")
                    
                    # 创建报告ID（使用时间戳）
                    report_id = f"report_{timestamp}"
                    
                    # 创建报告元数据
                    report_metadata = {
                        "env": args.env,
                        "timestamp": timestamp,
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "executed": 0  # 添加一个字段，记录实际执行的用例数
                    }
                    
                    # 如果使用了Allure报告，尝试从Allure结果目录中解析测试结果
                    import json
                    import glob
                    
                    # 查找所有测试结果JSON文件
                    result_files = glob.glob(f"{allure_results_dir}/*.json")
                    
                    for file_path in result_files:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                # 只处理测试结果文件
                                if 'status' in data:
                                    report_metadata["total"] += 1
                                    
                                    if data['status'].lower() == 'passed':
                                        report_metadata["passed"] += 1
                                    elif data['status'].lower() == 'failed' or data['status'].lower() == 'broken':
                                        report_metadata["failed"] += 1
                                    elif data['status'].lower() == 'skipped':
                                        report_metadata["skipped"] += 1
                        except Exception as e:
                            logger.error(f"解析测试结果文件失败: {str(e)}")
                    
                    # 添加报告持续时间
                    report_metadata["duration"] = duration
                    
                    # 计算实际执行的用例数（总数减去跳过的）
                    report_metadata["executed"] = report_metadata["total"] - report_metadata["skipped"]
                    
                    # 假设报告服务已在Docker中运行，直接上传报告
                    try:
                        # 直接使用add_report函数，不需要启动服务器
                        from utils.notification import add_report
                        
                        # 添加报告并获取URL
                        # 从配置中获取报告服务器URL
                        config = load_config()
                        report_server_url = config.get('report_server', {}).get('url', 'http://localhost:7987')
                        
                        report_url = add_report(report_id, abs_report_dir, report_metadata)
                        if report_url:
                            logger.info(f"报告已上传到服务器，可通过以下URL访问: {report_url}")
                            allure_report_url = report_url
                        else:
                            logger.warning("上传报告到服务器失败，将使用本地文件路径")
                            # 提供本地文件路径和Docker服务器URL
                            logger.info(f"您可以手动访问: {report_server_url}/{report_id}")
                    except Exception as e:
                        logger.error(f"上传报告到服务器失败: {str(e)}")
                        logger.warning("将使用本地文件路径")
                
                except Exception as e:
                    logger.error(f"处理报告服务器失败: {str(e)}")
            
            # 如果需要在浏览器中打开报告
            if args.open:
                logger.info("在浏览器中打开Allure报告...")
                
                try:
                    # 使用Allure的完整路径来启动服务
                    logger.info(f"执行命令: {allure_bin} serve {abs_results_dir}")
                    
                    # 创建进程配置
                    startupinfo = None
                    if sys.platform.startswith('win'):
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    # 运行allure serve命令
                    process = subprocess.Popen(
                        [allure_bin, "serve", abs_results_dir],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        startupinfo=startupinfo
                    )
                    
                    logger.info("Allure服务已在后台启动，稍后将在浏览器中打开")
                    
                except Exception as e:
                    logger.error(f"启动Allure服务失败: {str(e)}")
                    logger.info(f"请手动运行以下命令查看报告: {allure_bin} serve {abs_results_dir}")
        
        except Exception as e:
            logger.error(f"生成Allure报告失败: {str(e)}")
    
    # 收集测试结果统计信息
    try:
        # 从pytest的终端输出中解析测试结果
        test_summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "executed": 0,  # 添加实际执行的用例数
            "duration": duration,
            "env": args.env
        }
        
        # 如果使用了Allure报告，尝试从Allure结果目录中解析测试结果
        if args.allure:
            import json
            import glob
            
            # 查找所有测试结果JSON文件
            result_files = glob.glob(f"{allure_results_dir}/*.json")
            logger.info(f"找到 {len(result_files)} 个测试结果JSON文件")
            
            # 用于跟踪已处理的测试用例
            processed_tests = {}  # 使用字典存储每个测试用例的最新状态
            
            for file_path in result_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 只处理测试结果文件，并且确保不重复计算
                        if 'status' in data and ('fullName' in data or 'name' in data):
                            # 使用fullName作为测试用例的唯一标识符，如果没有则使用name
                            test_id = data.get('fullName', data.get('name', ''))
                            
                            if test_id:
                                # 更新或添加测试用例状态
                                processed_tests[test_id] = data['status'].lower()
                except Exception as e:
                    logger.error(f"解析测试结果文件失败: {str(e)}")
            
            # 计算最终统计结果
            test_summary["total"] = len(processed_tests)
            
            for status in processed_tests.values():
                if status == 'passed':
                    test_summary["passed"] += 1
                elif status == 'failed' or status == 'broken':
                    test_summary["failed"] += 1
                elif status == 'skipped':
                    test_summary["skipped"] += 1
            
            # 添加重试信息
            retry_count = len(result_files) - len(processed_tests)
            if retry_count > 0:
                test_summary["retry_count"] = retry_count
                logger.info(f"检测到 {retry_count} 次测试重试")
            
            logger.info(f"去重后有 {len(processed_tests)} 个唯一测试用例")
            logger.info(f"测试统计: 总数={test_summary['total']}, 通过={test_summary['passed']}, 失败={test_summary['failed']}, 跳过={test_summary['skipped']}")
        
        # 计算实际执行的用例数（总数减去跳过的）
        test_summary["executed"] = test_summary["total"] - test_summary["skipped"]
            
        # 如果有报告URL，添加到测试摘要中
        if allure_report_url:
            test_summary["report_url"] = allure_report_url
        
        # 发送测试报告到钉钉群
        if args.dingtalk:
            try:
                from utils.notification.dingtalk import get_default_dingtalk_sender
                
                logger.info("发送测试报告到钉钉群...")
                sender = get_default_dingtalk_sender()
                sender.send_test_report(test_summary)
                logger.info("测试报告已发送到钉钉群")
            except Exception as e:
                logger.error(f"发送测试报告到钉钉群失败: {str(e)}")
    
    except Exception as e:
        logger.error(f"处理测试结果失败: {str(e)}")
    
    # 记录测试结束
    logger.info("=" * 80)
    logger.info(f"测试执行完成，退出代码: {exit_code}")
    logger.info(f"总耗时: {duration // 60}分{duration % 60}秒")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 