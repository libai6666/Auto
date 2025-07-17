#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import random
import string
import re
from datetime import datetime
from utils.logger import logger

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_config(config_file="config.yaml"):
    """
    加载配置文件
    :param config_file: 配置文件名
    :return: 配置数据
    """
    config_path = os.path.join(PROJECT_ROOT, "config", config_file)
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}


def load_db_config():
    """
    加载数据库配置
    :return: 数据库配置
    """
    return load_config("db_config.yaml")


def load_test_data(file_path, key=None):
    """
    加载测试数据
    :param file_path: 数据文件路径
    :param key: 数据键
    :return: 测试数据
    """
    data_path = os.path.join(PROJECT_ROOT, "data", "api_data", file_path)
    
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if key:
            if key in data:
                return data[key]
            else:
                logger.error(f"数据键不存在: {key}")
                return None
        
        return data
    except Exception as e:
        logger.error(f"加载测试数据失败: {str(e)}")
        return None


def save_test_data(file_path, data):
    """
    保存测试数据
    :param file_path: 数据文件路径
    :param data: 要保存的数据
    :return: 成功返回True，失败返回False
    """
    data_path = os.path.join(PROJECT_ROOT, "data", "api_data", file_path)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"保存测试数据失败: {str(e)}")
        return False


def generate_random_string(length=8):
    """
    生成随机字符串
    :param length: 字符串长度
    :return: 随机字符串
    """
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def generate_random_phone():
    """
    生成随机手机号
    :return: 随机手机号
    """
    # 中国手机号格式
    prefix = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
              "150", "151", "152", "153", "155", "156", "157", "158", "159",
              "170", "176", "177", "178", "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
    
    return random.choice(prefix) + ''.join(random.choice(string.digits) for _ in range(8))


def generate_random_email(domain="example.com"):
    """
    生成随机邮箱
    :param domain: 邮箱域名
    :return: 随机邮箱
    """
    username = generate_random_string(8).lower()
    return f"{username}@{domain}"


def replace_variables(data, variables=None):
    """
    替换数据中的变量
    :param data: 原始数据
    :param variables: 变量字典
    :return: 替换后的数据
    """
    if variables is None:
        variables = {}
    
    # 添加内置变量
    built_in_vars = {
        "random_str": generate_random_string(),
        "timestamp": int(datetime.now().timestamp()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "random_phone": generate_random_phone(),
        "random_email": generate_random_email(),
    }
    
    # 合并变量
    all_vars = {**built_in_vars, **variables}
    
    # 如果数据是字符串，直接替换
    if isinstance(data, str):
        # 替换格式为 {变量名}
        pattern = r"\{([a-zA-Z0-9_]+)\}"
        
        def replace_var(match):
            var_name = match.group(1)
            return str(all_vars.get(var_name, match.group(0)))
        
        return re.sub(pattern, replace_var, data)
    
    # 如果数据是字典，递归替换
    elif isinstance(data, dict):
        return {k: replace_variables(v, all_vars) for k, v in data.items()}
    
    # 如果数据是列表，递归替换
    elif isinstance(data, list):
        return [replace_variables(item, all_vars) for item in data]
    
    # 其他类型直接返回
    return data


def extract_data(response, extract_rules):
    """
    从响应中提取数据
    :param response: 响应对象
    :param extract_rules: 提取规则
    :return: 提取的变量字典
    """
    extracted_vars = {}
    
    if not extract_rules:
        return extracted_vars
    
    try:
        # 获取响应体
        try:
            response_body = response.json()
        except:
            response_body = response.text
        
        # 遍历提取规则
        for var_name, rule in extract_rules.items():
            # 处理JSON路径提取
            if rule.startswith("$."):
                import jsonpath
                result = jsonpath.jsonpath(response_body, rule)
                if result and len(result) > 0:
                    extracted_vars[var_name] = result[0]
                else:
                    logger.warning(f"无法提取变量 {var_name}, 路径: {rule}")
            
            # 处理正则表达式提取
            elif rule.startswith("regex:"):
                regex = rule[6:]
                match = re.search(regex, response.text)
                if match:
                    extracted_vars[var_name] = match.group(1)
                else:
                    logger.warning(f"无法提取变量 {var_name}, 正则: {regex}")
            
            # 处理响应头提取
            elif rule.startswith("header:"):
                header_name = rule[7:]
                if header_name in response.headers:
                    extracted_vars[var_name] = response.headers[header_name]
                else:
                    logger.warning(f"无法提取变量 {var_name}, 响应头: {header_name}")
            
            # 处理状态码提取
            elif rule == "status_code":
                extracted_vars[var_name] = response.status_code
            
            # 处理响应时间提取
            elif rule == "response_time":
                extracted_vars[var_name] = response.elapsed.total_seconds()
            
            # 处理响应体提取
            elif rule == "response_body":
                extracted_vars[var_name] = response_body
            
            # 其他情况当作属性处理
            else:
                logger.warning(f"未知的提取规则: {rule}")
    
    except Exception as e:
        logger.error(f"提取变量失败: {str(e)}")
    
    return extracted_vars 

def load_yaml_data(file_path):
    """
    加载YAML文件数据
    :param file_path: YAML文件路径（相对于项目根目录）
    :return: 加载的数据
    """
    yaml_path = os.path.join(PROJECT_ROOT, file_path)
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        logger.error(f"加载YAML数据失败: {str(e)}")
        return None 