#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报告清理工具
用于定期清理旧的测试报告
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("report_cleaner")


def load_reports_index(reports_dir):
    """
    加载报告索引文件
    :param reports_dir: 报告目录
    :return: 报告索引字典
    """
    index_file = os.path.join(reports_dir, "reports_index.json")
    if not os.path.exists(index_file):
        logger.warning(f"报告索引文件不存在: {index_file}")
        return {}
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载报告索引失败: {str(e)}")
        return {}


def save_reports_index(reports_dir, reports_index):
    """
    保存报告索引文件
    :param reports_dir: 报告目录
    :param reports_index: 报告索引字典
    """
    index_file = os.path.join(reports_dir, "reports_index.json")
    
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(reports_index, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存报告索引，共 {len(reports_index)} 个报告")
    except Exception as e:
        logger.error(f"保存报告索引失败: {str(e)}")


def clean_old_reports(reports_dir, retention_days=30, dry_run=False):
    """
    清理旧的报告
    :param reports_dir: 报告目录
    :param retention_days: 保留天数
    :param dry_run: 是否仅模拟运行
    :return: 清理的报告数量
    """
    if not os.path.exists(reports_dir):
        logger.error(f"报告目录不存在: {reports_dir}")
        return 0
    
    # 加载报告索引
    reports_index = load_reports_index(reports_dir)
    if not reports_index:
        logger.warning("报告索引为空，无需清理")
        return 0
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    logger.info(f"清理 {retention_days} 天前的报告，截止日期: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # 统计
    total_reports = len(reports_index)
    removed_reports = 0
    updated_index = {}
    
    # 遍历报告
    for report_id, report_info in reports_index.items():
        # 获取报告创建时间
        created_at = report_info.get("created_at")
        if not created_at:
            logger.warning(f"报告 {report_id} 没有创建时间信息，将保留")
            updated_index[report_id] = report_info
            continue
        
        try:
            # 解析创建时间
            report_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            
            # 检查是否超过保留期限
            if report_date < cutoff_date:
                report_dir = os.path.join(reports_dir, report_id)
                
                if dry_run:
                    logger.info(f"[模拟] 将删除报告: {report_id}, 创建于 {created_at}")
                else:
                    # 删除报告目录
                    if os.path.exists(report_dir):
                        logger.info(f"删除报告目录: {report_dir}")
                        shutil.rmtree(report_dir)
                    else:
                        logger.warning(f"报告目录不存在: {report_dir}")
                
                removed_reports += 1
            else:
                # 保留报告
                updated_index[report_id] = report_info
        except Exception as e:
            logger.error(f"处理报告 {report_id} 失败: {str(e)}")
            # 出错时保留报告
            updated_index[report_id] = report_info
    
    # 保存更新后的索引
    if not dry_run and removed_reports > 0:
        save_reports_index(reports_dir, updated_index)
        
        # 重新生成索引HTML
        try:
            from utils.notification.report_server import get_report_server
            server = get_report_server(reports_dir)
            server.generate_index_html()
            logger.info("已重新生成索引HTML")
        except Exception as e:
            logger.error(f"重新生成索引HTML失败: {str(e)}")
    
    # 打印统计信息
    logger.info(f"报告清理完成，共 {total_reports} 个报告，清理了 {removed_reports} 个报告，剩余 {total_reports - removed_reports} 个报告")
    
    return removed_reports


def parse_args():
    """
    解析命令行参数
    :return: 解析结果
    """
    parser = argparse.ArgumentParser(description="测试报告清理工具")
    
    parser.add_argument("--dir", "-d", default="reports",
                        help="报告根目录")
    parser.add_argument("--days", "-D", type=int, default=30,
                        help="报告保留天数")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅模拟运行，不实际删除文件")
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 确保使用绝对路径
    reports_dir = os.path.abspath(args.dir)
    
    # 日志记录
    logger.info("=" * 80)
    logger.info("开始清理测试报告")
    logger.info(f"报告目录: {reports_dir}")
    logger.info(f"保留天数: {args.days}")
    logger.info(f"模拟运行: {args.dry_run}")
    
    # 清理报告
    clean_old_reports(reports_dir, args.days, args.dry_run)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 