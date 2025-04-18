#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import subprocess
import pytest
import webbrowser
from datetime import datetime
from utils.logger import logger


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
        
        try:
            subprocess.run(["allure", "generate", allure_results_dir, "-o", allure_report_dir, "--clean"],
                           check=True)
            logger.info(f"Allure报告已生成: {allure_report_dir}")
            
            # 打开报告
            if args.open:
                logger.info("在浏览器中打开Allure报告...")
                if sys.platform.startswith('win'):
                    os.system(f"start allure serve {allure_results_dir}")
                elif sys.platform.startswith('darwin'):
                    os.system(f"open -a 'Google Chrome' {allure_report_dir}")
                else:
                    webbrowser.open_new_tab(f"file://{os.path.abspath(allure_report_dir)}/index.html")
        except subprocess.CalledProcessError as e:
            logger.error(f"生成Allure报告失败: {str(e)}")
            logger.error("请确保已安装Allure命令行工具")
        except Exception as e:
            logger.error(f"处理Allure报告时出错: {str(e)}")
    
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