#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import os
import json
import allure
from datetime import datetime

from utils.api_client import APIClient
from utils.logger import logger, setup_logger, cleanup_logs
from utils.data_handler import load_config
from utils.db_utils import MySQLHandler
from utils.client_factory import ClientFactory
from utils.app.heartbeat import stop_all_heartbeats

# 初始化日志
logger = setup_logger()

# 测试会话数据
session_data = {}


@pytest.fixture(scope="session", autouse=True)
def cleanup_old_logs():
    """
    在测试会话开始前自动清理旧的日志文件
    """
    logger.info("正在运行自动日志清理...")
    cleanup_logs()
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_heartbeats():
    """
    在测试会话结束时自动清理所有心跳线程
    """
    # 测试开始前不做任何事
    yield
    
    # 测试结束后停止所有心跳线程
    logger.info("测试会话结束，正在清理所有心跳线程...")
    stop_all_heartbeats()


def pytest_configure(config):
    """
    Pytest配置函数
    :param config: 配置对象
    """
    # 配置Allure报告相关信息
    logger.info("配置Allure报告...")
    # 注释掉有问题的部分
    # allure.environment(
    #     python_version=os.environ.get("PYTHON_VERSION", "3.8+"),
    #     pytest_version=pytest.__version__,
    #     platform=os.environ.get("PLATFORM", "Windows"),
    #     environment=load_config().get("current_env", "test")
    # )


@pytest.fixture(scope="session")
def api_client():
    """
    API客户端夹具
    :return: APIClient实例
    """
    # 加载配置
    config = load_config()
    
    # 获取当前环境配置
    current_env = config.get("current_env", "test")
    env_config = config.get("env_config", {}).get(current_env, {})
    
    # 创建客户端实例
    logger.info(f"创建API客户端，环境: {current_env}, 基础URL: {env_config.get('base_url')}")
    client = APIClient(
        base_url=env_config.get("base_url"),
        timeout=env_config.get("timeout", 10)
    )
    
    # 返回客户端实例
    yield client
    
    # 测试结束后关闭会话
    client.session.close()
    logger.info("API客户端会话已关闭")


@pytest.fixture(scope="session")
def client_factory():
    """
    客户端工厂夹具 - 用于创建任意用户的客户端
    :return: ClientFactory实例
    """
    factory = ClientFactory()
    yield factory


@pytest.fixture(scope="session")
def db_handler():
    """
    数据库处理器夹具
    :return: MySQLHandler实例
    """
    # 加载配置
    config = load_config()
    
    # 获取当前环境
    current_env = config.get("current_env", "test")
    
    # 创建数据库处理器实例
    logger.info(f"创建数据库处理器，环境: {current_env}")
    handler = MySQLHandler(env=current_env)
    
    # 返回处理器实例
    yield handler
    
    # 测试结束后关闭连接
    handler.close()
    logger.info("数据库连接已关闭")


@pytest.fixture(scope="session")
def session_variables():
    """
    会话变量夹具
    :return: 会话变量字典
    """
    # 初始化会话变量
    variables = {}
    
    # 返回变量字典
    return variables


@pytest.fixture(scope="function", autouse=True)
def function_setup_teardown(request):
    """
    测试功能函数的前置和后置处理
    :param request: 请求对象
    """
    # 获取测试函数名
    func_name = request.function.__name__
    
    # 获取测试类名（如果有）
    if request.cls:
        class_name = request.cls.__name__
        test_name = f"{class_name}.{func_name}"
    else:
        test_name = func_name
    
    # 获取测试模块名
    module_name = request.module.__name__
    
    # 记录测试开始
    logger.info(f"开始执行测试: {module_name}.{test_name}")
    
    # 测试执行前处理
    start_time = datetime.now()
    
    # 执行测试
    yield
    
    # 测试执行后处理
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 记录测试结束
    logger.info(f"测试执行完成: {module_name}.{test_name}, 耗时: {duration:.2f}秒")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试报告处理钩子
    :param item: 测试项
    :param call: 调用信息
    """
    # 执行其他钩子
    outcome = yield
    
    # 获取报告对象
    report = outcome.get_result()
    
    # 获取测试阶段
    test_fn = item.obj
    docstring = getattr(test_fn, '__doc__', "")
    
    # 为失败的测试添加额外信息
    if report.when == "call" and report.failed:
        # 添加详细日志
        logger.error(f"测试失败: {item.nodeid}")
        
        # 添加Allure附件（如果有异常信息）
        if hasattr(report, "wasxfail"):
            # 预期失败的测试
            pass
        else:
            if call.excinfo:
                # 添加异常信息
                allure.attach(
                    str(call.excinfo),
                    name="异常信息",
                    attachment_type=allure.attachment_type.TEXT
                )


def pytest_addoption(parser):
    """
    添加命令行选项
    :param parser: 解析器对象
    """
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="指定测试环境: dev, test 或 prod"
    )


@pytest.fixture(scope="session", autouse=True)
def set_environment(request):
    """
    设置测试环境
    :param request: 请求对象
    """
    # 获取命令行参数
    env = request.config.getoption("--env")
    
    if env:
        # 加载配置
        config = load_config()
        
        # 修改当前环境
        config["current_env"] = env
        
        # 记录环境设置
        logger.info(f"通过命令行设置环境: {env}")
        
        # 设置环境变量
        os.environ["TEST_ENV"] = env