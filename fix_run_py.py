#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本用于修复run.py中的语法错误。
运行方法：python fix_run_py.py
"""

import os
import re

def fix_run_py():
    file_path = "run.py"
    
    # 读取原文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_path = file_path + ".bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已备份原文件到: {backup_path}")
    
    # 修复问题区域的代码
    pattern = r'except Exception as e:.*?logger\.error\(f"生成Allure报告失败: \{str\(e\)\}"\)(\s+)# 收集测试结果统计信息'
    fixed_content = re.sub(pattern, 
                           'except Exception as e:\n            logger.error(f"生成Allure报告失败: {str(e)}")\n    \n    # 收集测试结果统计信息',
                           content, 
                           flags=re.DOTALL)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"已修复文件: {file_path}")
    print("请尝试重新运行: python run.py --allure --dingtalk")

if __name__ == "__main__":
    fix_run_py() 