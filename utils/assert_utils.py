#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import jsonpath
from utils.logger import logger


def assert_status_code(response, expected_status_code):
    """
    断言响应状态码
    :param response: 响应对象
    :param expected_status_code: 期望的状态码
    :return: 断言结果, 成功返回True，失败返回False
    """
    actual_status_code = response.status_code
    
    if actual_status_code == expected_status_code:
        logger.info(f"状态码断言成功: 期望 {expected_status_code}, 实际 {actual_status_code}")
        return True
    else:
        logger.error(f"状态码断言失败: 期望 {expected_status_code}, 实际 {actual_status_code}")
        return False


def assert_contains(response, expected_text):
    """
    断言响应包含指定文本
    :param response: 响应对象
    :param expected_text: 期望包含的文本
    :return: 断言结果
    """
    response_text = response.text
    
    if expected_text in response_text:
        logger.info(f"包含断言成功: 响应包含 '{expected_text}'")
        return True
    else:
        logger.error(f"包含断言失败: 响应不包含 '{expected_text}'")
        return False


def assert_json_value(response, json_path, expected_value):
    """
    断言JSON值
    :param response: 响应对象
    :param json_path: JSON路径
    :param expected_value: 期望值
    :return: 断言结果
    """
    try:
        actual_json = response.json()
    except Exception as e:
        logger.error(f"JSON断言失败: 响应不是有效的JSON格式 - {str(e)}")
        return False
    
    try:
        result = jsonpath.jsonpath(actual_json, json_path)
        
        if not result:
            logger.error(f"JSON断言失败: 路径 '{json_path}' 不存在")
            return False
        
        actual_value = result[0]
        
        # 特殊断言符号处理
        if isinstance(expected_value, str) and expected_value.startswith("~"):
            symbol = expected_value[1:]
            
            # ~exist: 字段存在
            if symbol == "exist":
                if actual_value is not None:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 存在")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 应该存在")
                    return False
            
            # ~not_exist: 字段不存在
            elif symbol == "not_exist":
                if actual_value is None:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 不存在")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 不应该存在")
                    return False
            
            # ~null: 字段为null
            elif symbol == "null":
                if actual_value is None:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值为 null")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不为 null")
                    return False
            
            # ~not_null: 字段不为null
            elif symbol == "not_null":
                if actual_value is not None:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值不为 null")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值为 null")
                    return False
            
            # ~regex: 字段匹配正则表达式
            elif symbol.startswith("regex:"):
                regex = symbol[6:]
                if isinstance(actual_value, str) and re.match(regex, actual_value):
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值匹配正则 '{regex}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不匹配正则 '{regex}'")
                    return False
            
            # ~type: 字段类型
            elif symbol.startswith("type:"):
                type_name = symbol[5:]
                type_mapping = {
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                }
                
                expected_type = type_mapping.get(type_name)
                if expected_type and isinstance(actual_value, expected_type):
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值类型为 '{type_name}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值类型不是 '{type_name}'")
                    return False
            
            # ~contains: 字段包含字符串
            elif symbol.startswith("contains:"):
                substr = symbol[9:]
                if isinstance(actual_value, str) and substr in actual_value:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值包含 '{substr}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不包含 '{substr}'")
                    return False
            
            # ~not_contains: 字段不包含字符串
            elif symbol.startswith("not_contains:"):
                substr = symbol[13:]
                if isinstance(actual_value, str) and substr not in actual_value:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值不包含 '{substr}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值包含 '{substr}'")
                    return False
            
            # ~in: 字段在列表中
            elif symbol.startswith("in:"):
                value_list = symbol[3:].split(",")
                if str(actual_value) in value_list:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值在列表 '{value_list}' 中")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不在列表 '{value_list}' 中")
                    return False
            
            # ~not_in: 字段不在列表中
            elif symbol.startswith("not_in:"):
                value_list = symbol[7:].split(",")
                if str(actual_value) not in value_list:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值不在列表 '{value_list}' 中")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值在列表 '{value_list}' 中")
                    return False
            
            # ~greater_than: 字段大于
            elif symbol.startswith("greater_than:"):
                threshold = float(symbol[13:])
                if isinstance(actual_value, (int, float)) and actual_value > threshold:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值大于 '{threshold}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不大于 '{threshold}'")
                    return False
            
            # ~less_than: 字段小于
            elif symbol.startswith("less_than:"):
                threshold = float(symbol[10:])
                if isinstance(actual_value, (int, float)) and actual_value < threshold:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值小于 '{threshold}'")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不小于 '{threshold}'")
                    return False
            
            # 未知断言符号
            else:
                logger.error(f"JSON断言失败: 未知的断言符号 '{symbol}'")
                return False
        
        # 正常值比较
        else:
            # 特殊处理JSON对象和列表的比较
            if isinstance(expected_value, (dict, list)) and isinstance(actual_value, (dict, list)):
                expected_json = json.dumps(expected_value, sort_keys=True)
                actual_json = json.dumps(actual_value, sort_keys=True)
                
                if expected_json == actual_json:
                    logger.info(f"JSON断言成功: 路径 '{json_path}' 值匹配")
                    return True
                else:
                    logger.error(f"JSON断言失败: 路径 '{json_path}' 值不匹配")
                    logger.error(f"期望: {expected_json}")
                    logger.error(f"实际: {actual_json}")
                    return False
            
            # 其他类型的比较
            if actual_value == expected_value:
                logger.info(f"JSON断言成功: 路径 '{json_path}' 值匹配")
                return True
            else:
                logger.error(f"JSON断言失败: 路径 '{json_path}' 值不匹配, 期望 '{expected_value}', 实际 '{actual_value}'")
                return False
    
    except Exception as e:
        logger.error(f"JSON断言异常: {str(e)}")
        return False


def assert_json(response, json_path_dict):
    """
    批量断言JSON值
    :param response: 响应对象
    :param json_path_dict: JSON路径和期望值的字典
    :return: 断言结果
    """
    result = True
    
    for json_path, expected_value in json_path_dict.items():
        if not assert_json_value(response, json_path, expected_value):
            result = False
    
    return result


def assert_response(response, expected):
    """
    综合断言响应
    :param response: 响应对象
    :param expected: 期望结果字典
    :return: 断言结果
    """
    result = True
    
    # 断言状态码
    if "status_code" in expected:
        if not assert_status_code(response, expected["status_code"]):
            result = False
    
    # 断言包含文本
    if "contains" in expected:
        if not assert_contains(response, expected["contains"]):
            result = False
    
    # 断言不包含文本
    if "not_contains" in expected:
        if assert_contains(response, expected["not_contains"]):
            logger.error(f"包含断言失败: 响应不应包含 '{expected['not_contains']}'")
            result = False
    
    # 断言JSON
    if "json" in expected:
        try:
            json_data = response.json()
            
            for key, value in expected["json"].items():
                path = f"$.{key}"
                if not assert_json_value(response, path, value):
                    result = False
        except Exception as e:
            logger.error(f"JSON断言异常: {str(e)}")
            result = False
    
    # 断言响应时间
    if "response_time_less_than" in expected:
        time_threshold = float(expected["response_time_less_than"])
        actual_time = response.elapsed.total_seconds()
        
        if actual_time < time_threshold:
            logger.info(f"响应时间断言成功: 响应时间 {actual_time}s 小于 {time_threshold}s")
        else:
            logger.error(f"响应时间断言失败: 响应时间 {actual_time}s 不小于 {time_threshold}s")
            result = False
    
    return result 