#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PostgreSQL数据库连接测试脚本
"""

import sys
import os
import socket
import traceback
import subprocess
import platform
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.logger import logger
from utils.data_handler import load_db_config

def ping_host(host):
    """
    测试与主机的网络连通性
    :param host: 主机名或IP地址
    :return: 是否可以ping通，延迟时间
    """
    logger.info(f"测试与主机 {host} 的网络连通性...")
    
    # 根据操作系统选择ping命令参数
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', host]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Ping {host} 成功")
            # 尝试提取延迟时间
            output = result.stdout
            logger.info(f"Ping输出:\n{output}")
            return True, output
        else:
            logger.error(f"Ping {host} 失败")
            logger.error(f"错误输出:\n{result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Ping {host} 超时")
        return False, "Ping命令超时"
    except Exception as e:
        logger.error(f"执行Ping命令异常: {str(e)}")
        return False, str(e)

def test_tcp_connection(host, port, timeout=5):
    """
    测试TCP连接
    :param host: 主机名或IP地址
    :param port: 端口号
    :param timeout: 超时时间（秒）
    :return: 是否可以连接
    """
    logger.info(f"测试TCP连接 {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"TCP连接到 {host}:{port} 成功")
            return True
        else:
            logger.error(f"TCP连接到 {host}:{port} 失败，错误码: {result}")
            return False
    except socket.gaierror:
        logger.error(f"主机名解析失败: {host}")
        return False
    except socket.timeout:
        logger.error(f"连接超时: {host}:{port}")
        return False
    except Exception as e:
        logger.error(f"测试TCP连接异常: {str(e)}")
        return False

def verify_postgresql_config():
    """验证PostgreSQL配置是否存在且格式正确"""
    logger.info("验证PostgreSQL配置...")
    
    try:
        # 加载数据库配置
        db_config = load_db_config()
        
        # 检查PostgreSQL配置是否存在
        if "postgresql" not in db_config["db_config"]:
            logger.error("找不到PostgreSQL配置，请检查config/db_config.yaml文件")
            return False, None
        
        # 检查test环境配置
        if "test" not in db_config["db_config"]["postgresql"]:
            logger.error("找不到PostgreSQL的test环境配置")
            return False, None
        
        # 获取test环境配置
        pg_config = db_config["db_config"]["postgresql"]["test"]
        
        # 检查必要字段
        required_fields = ["host", "port", "user", "password", "database"]
        missing_fields = [field for field in required_fields if field not in pg_config]
        
        if missing_fields:
            logger.error(f"PostgreSQL配置缺少必要字段: {', '.join(missing_fields)}")
            return False, None
        
        # 显示配置信息
        logger.info(f"PostgreSQL配置验证成功:")
        logger.info(f"Host: {pg_config['host']}")
        logger.info(f"Port: {pg_config['port']}")
        logger.info(f"Database: {pg_config['database']}")
        logger.info(f"User: {pg_config['user']}")
        logger.info(f"Password: {'*' * len(pg_config['password'])}")
        
        # 添加本地IP信息
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            logger.info(f"本地IP地址: {local_ip}")
        except Exception as e:
            logger.error(f"获取本地IP地址失败: {str(e)}")
        
        # 检查DNS解析
        try:
            host_ip = socket.gethostbyname(pg_config['host'])
            logger.info(f"数据库主机名 {pg_config['host']} 解析到IP: {host_ip}")
        except socket.gaierror:
            logger.warning(f"无法解析数据库主机名 {pg_config['host']} 到IP地址")
            # 如果无法解析主机名，但主机名看起来像IP，则继续
            if not all(c.isdigit() or c == '.' for c in pg_config['host']):
                logger.error("主机名不是有效的IP地址格式，且无法解析到IP")
        except Exception as e:
            logger.error(f"检查主机名解析时出错: {str(e)}")
        
        return True, pg_config
    except Exception as e:
        logger.error(f"验证PostgreSQL配置失败: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False, None

def test_postgresql_connection():
    """测试PostgreSQL数据库连接"""
    logger.info("开始测试PostgreSQL数据库连接...")
    
    try:
        # 验证配置
        config_ok, pg_config = verify_postgresql_config()
        if not config_ok or pg_config is None:
            return False
        
        # 网络连通性测试
        ping_result, ping_output = ping_host(pg_config['host'])
        
        # TCP连接测试
        tcp_ok = test_tcp_connection(pg_config['host'], pg_config['port'])
        
        if not tcp_ok:
            logger.error("TCP连接测试失败，请检查网络连接和防火墙设置")
            logger.error("可能需要将您的IP添加到华为云的安全组白名单中")
            return False
        
        # 导入psycopg2
        try:
            import psycopg2
            import psycopg2.extras
            logger.info(f"已成功导入psycopg2库，版本: {psycopg2.__version__}")
        except ImportError:
            logger.error("未安装psycopg2模块，无法测试实际连接")
            logger.info("请使用以下命令安装psycopg2:")
            logger.info("pip install psycopg2-binary")
            return False
        
        # 创建PostgreSQL连接
        logger.info("尝试连接到PostgreSQL数据库...")
        
        # 直接使用psycopg2连接，以获取更详细的错误信息
        try:
            conn = psycopg2.connect(
                host=pg_config['host'],
                port=pg_config['port'],
                user=pg_config['user'],
                password=pg_config['password'],
                database=pg_config['database'],
                sslmode=pg_config.get('sslmode', 'prefer'),
                connect_timeout=10  # 增加连接超时设置
            )
            logger.info("PostgreSQL直接连接成功!")
            conn.close()
        except Exception as e:
            logger.error(f"PostgreSQL直接连接失败: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            
            # 根据错误类型提供建议
            error_str = str(e).lower()
            if "timeout" in error_str:
                logger.error("连接超时，请检查网络连接和防火墙设置")
                logger.error("需要将您的IP添加到华为云的安全组白名单中")
            elif "password authentication failed" in error_str:
                logger.error("密码认证失败，请检查用户名和密码")
            elif "no pg_hba.conf entry" in error_str:
                logger.error("没有pg_hba.conf项，需要在PostgreSQL服务器上配置允许您的IP连接")
            elif "connection refused" in error_str:
                logger.error("连接被拒绝，请检查数据库服务是否运行，以及防火墙设置")
            
            return False
        
        # 使用工具类测试连接
        from utils.db_utils import PostgreSQLHandler
        pg_handler = PostgreSQLHandler(env="test")
        
        # 测试连接
        conn = pg_handler.connect()
        logger.info("PostgreSQL连接成功!")
        
        # 测试查询
        try:
            # 简单的测试查询，获取当前数据库版本
            result = pg_handler.fetch_one("SELECT version();")
            logger.info(f"PostgreSQL版本: {result['version']}")
            
            # 列出数据库中的所有表
            tables = pg_handler.execute_query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            if tables:
                logger.info(f"数据库中的表数量: {len(tables)}")
                logger.info("表列表:")
                for table in tables:
                    logger.info(f"- {table['table_name']}")
            else:
                logger.info("数据库中没有表")
                
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            logger.error(f"异常详情: {traceback.format_exc()}")
        
        # 关闭连接
        pg_handler.close()
        logger.info("测试完成")
        
        return True
    except Exception as e:
        logger.error(f"PostgreSQL连接测试失败: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # 验证配置
    config_ok, pg_config = verify_postgresql_config()
    
    if not config_ok:
        logger.error("PostgreSQL配置验证失败!")
        sys.exit(1)
    
    logger.info("PostgreSQL配置验证成功!")
    
    # 尝试测试连接（如果psycopg2可用）
    try:
        import psycopg2
        success = test_postgresql_connection()
        
        if success:
            logger.info("PostgreSQL连接测试成功!")
            sys.exit(0)
        else:
            logger.error("PostgreSQL连接测试失败!")
            sys.exit(1)
    except ImportError:
        logger.warning("未安装psycopg2，跳过连接测试")
        logger.info("配置验证已通过，但未进行实际连接测试")
        logger.info("请使用以下命令安装psycopg2后再进行完整测试:")
        logger.info("pip install psycopg2-binary")
        sys.exit(0) 