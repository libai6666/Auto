#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
from pymysql.cursors import DictCursor
import sqlite3
from utils.logger import logger
from utils.data_handler import load_db_config


class MySQLHandler:
    """
    MySQL数据库操作工具类
    """

    def __init__(self, env="test", db_type="mysql"):
        """
        初始化数据库连接
        :param env: 环境名称，如test, dev, prod
        :param db_type: 数据库类型，如mysql, sqlite
        """
        # 加载数据库配置
        db_config = load_db_config()
        
        # 获取对应环境的数据库配置
        try:
            if db_type == "mysql":
                self.config = db_config["db_config"]["mysql"][env]
            elif db_type == "postgresql":
                # 这里让MySQL处理类也能识别postgresql类型，但不做处理
                logger.error(f"MySQL处理类不支持数据库类型: {db_type}，请使用PostgreSQLHandler")
                raise ValueError(f"MySQL处理类不支持数据库类型: {db_type}，请使用PostgreSQLHandler")
            else:
                logger.error(f"不支持的数据库类型: {db_type}")
                raise ValueError(f"不支持的数据库类型: {db_type}")
        except KeyError:
            logger.error(f"找不到数据库配置: env={env}, db_type={db_type}")
            raise ValueError(f"找不到数据库配置: env={env}, db_type={db_type}")
        
        # 数据库连接
        self.conn = None
    
    def connect(self):
        """
        建立数据库连接
        :return: 数据库连接对象
        """
        if self.conn is None:
            try:
                self.conn = pymysql.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    user=self.config["user"],
                    password=self.config["password"],
                    database=self.config["database"],
                    charset=self.config["charset"],
                    cursorclass=DictCursor
                )
                logger.info(f"MySQL数据库连接成功: {self.config['host']}:{self.config['port']}/{self.config['database']}")
            except Exception as e:
                logger.error(f"MySQL数据库连接失败: {str(e)}")
                raise
        
        return self.conn
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.info("MySQL数据库连接已关闭")
    
    def execute_query(self, sql, params=None):
        """
        执行查询SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 查询结果
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                result = cursor.fetchall()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"执行查询SQL成功: {sql}, 参数: {log_params}, 结果数: {len(result)}")
                
                return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"执行查询SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def execute_update(self, sql, params=None):
        """
        执行更新SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                if params:
                    affected_rows = cursor.execute(sql, params)
                else:
                    affected_rows = cursor.execute(sql)
                
                self.conn.commit()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"执行更新SQL成功: {sql}, 参数: {log_params}, 影响行数: {affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            log_params = params if params else ""
            logger.error(f"执行更新SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_one(self, sql, params=None):
        """
        查询单条记录
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单条记录
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                result = cursor.fetchone()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"查询单条记录成功: {sql}, 参数: {log_params}")
                
                return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"查询单条记录失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_value(self, sql, params=None):
        """
        查询单个值
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单个值
        """
        # 查询单条记录
        record = self.fetch_one(sql, params)
        
        if record:
            # 获取第一个字段的值
            return list(record.values())[0]
        
        return None
    
    def insert(self, table, data):
        """
        插入数据
        :param table: 表名
        :param data: 数据字典
        :return: 自增ID
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                placeholders = ", ".join(["%s"] * len(data))
                columns = ", ".join(f"`{column}`" for column in data.keys())
                values = list(data.values())
                
                sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
                
                # 执行SQL
                cursor.execute(sql, values)
                
                # 获取自增ID
                last_id = cursor.lastrowid
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"插入数据成功: 表={table}, 数据={data}, ID={last_id}")
                
                return last_id
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"插入数据失败: 表={table}, 数据={data}, 错误={str(e)}")
            raise
    
    def update(self, table, data, condition, condition_params=None):
        """
        更新数据
        :param table: 表名
        :param data: 要更新的数据字典
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                set_clause = ", ".join([f"`{column}` = %s" for column in data.keys()])
                values = list(data.values())
                
                sql = f"UPDATE `{table}` SET {set_clause} WHERE {condition}"
                
                # 合并参数
                if condition_params:
                    if isinstance(condition_params, list):
                        params = values + condition_params
                    else:
                        params = values + [condition_params]
                else:
                    params = values
                
                # 执行SQL
                affected_rows = cursor.execute(sql, params)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"更新数据成功: 表={table}, 数据={data}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"更新数据失败: 表={table}, 数据={data}, 条件={condition}, 错误={str(e)}")
            raise
    
    def delete(self, table, condition, condition_params=None):
        """
        删除数据
        :param table: 表名
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                sql = f"DELETE FROM `{table}` WHERE {condition}"
                
                # 执行SQL
                if condition_params:
                    affected_rows = cursor.execute(sql, condition_params)
                else:
                    affected_rows = cursor.execute(sql)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"删除数据成功: 表={table}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"删除数据失败: 表={table}, 条件={condition}, 错误={str(e)}")
            raise
    
    def execute_transaction(self, sql_list, params_list=None):
        """
        执行事务
        :param sql_list: SQL语句列表
        :param params_list: SQL参数列表
        :return: 是否成功
        """
        # 确保连接已建立
        self.connect()
        
        # 开始事务
        try:
            with self.conn.cursor() as cursor:
                for i, sql in enumerate(sql_list):
                    # 获取对应的参数
                    params = None
                    if params_list and i < len(params_list):
                        params = params_list[i]
                    
                    # 执行SQL
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"执行事务成功: SQL条数={len(sql_list)}")
                
                return True
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"执行事务失败: 错误={str(e)}")
            raise


class SQLiteHandler:
    """
    SQLite数据库操作工具类
    """

    def __init__(self, db_file=None):
        """
        初始化SQLite数据库连接
        :param db_file: 数据库文件路径
        """
        # 加载数据库配置
        if db_file is None:
            db_config = load_db_config()
            db_file = db_config["db_config"]["sqlite"]["db_file"]
        
        self.db_file = db_file
        self.conn = None
    
    def connect(self):
        """
        建立数据库连接
        :return: 数据库连接对象
        """
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_file)
                # 设置返回字典类型
                self.conn.row_factory = self._dict_factory
                
                logger.info(f"SQLite数据库连接成功: {self.db_file}")
            except Exception as e:
                logger.error(f"SQLite数据库连接失败: {str(e)}")
                raise
        
        return self.conn
    
    def _dict_factory(self, cursor, row):
        """
        将行转换为字典
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.info("SQLite数据库连接已关闭")
    
    def execute_query(self, sql, params=None):
        """
        执行查询SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 查询结果
        """
        # 确保连接已建立
        self.connect()
        
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            result = cursor.fetchall()
            cursor.close()
            
            # 记录日志
            log_params = params if params else ""
            logger.info(f"执行查询SQL成功: {sql}, 参数: {log_params}, 结果数: {len(result)}")
            
            return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"执行查询SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def execute_update(self, sql, params=None):
        """
        执行更新SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            affected_rows = cursor.rowcount
            self.conn.commit()
            cursor.close()
            
            # 记录日志
            log_params = params if params else ""
            logger.info(f"执行更新SQL成功: {sql}, 参数: {log_params}, 影响行数: {affected_rows}")
            
            return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            log_params = params if params else ""
            logger.error(f"执行更新SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_one(self, sql, params=None):
        """
        查询单条记录
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单条记录
        """
        # 确保连接已建立
        self.connect()
        
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            result = cursor.fetchone()
            cursor.close()
            
            # 记录日志
            log_params = params if params else ""
            logger.info(f"查询单条记录成功: {sql}, 参数: {log_params}")
            
            return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"查询单条记录失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_value(self, sql, params=None):
        """
        查询单个值
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单个值
        """
        # 查询单条记录
        record = self.fetch_one(sql, params)
        
        if record:
            # 获取第一个字段的值
            return list(record.values())[0]
        
        return None
    
    def insert(self, table, data):
        """
        插入数据
        :param table: 表名
        :param data: 数据字典
        :return: 自增ID
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                placeholders = ", ".join(["%s"] * len(data))
                columns = ", ".join(f"`{column}`" for column in data.keys())
                values = list(data.values())
                
                sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
                
                # 执行SQL
                cursor.execute(sql, values)
                
                # 获取自增ID
                last_id = cursor.lastrowid
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"插入数据成功: 表={table}, 数据={data}, ID={last_id}")
                
                return last_id
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"插入数据失败: 表={table}, 数据={data}, 错误={str(e)}")
            raise
    
    def update(self, table, data, condition, condition_params=None):
        """
        更新数据
        :param table: 表名
        :param data: 要更新的数据字典
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                set_clause = ", ".join([f"`{column}` = %s" for column in data.keys()])
                values = list(data.values())
                
                sql = f"UPDATE `{table}` SET {set_clause} WHERE {condition}"
                
                # 合并参数
                if condition_params:
                    if isinstance(condition_params, list):
                        params = values + condition_params
                    else:
                        params = values + [condition_params]
                else:
                    params = values
                
                # 执行SQL
                affected_rows = cursor.execute(sql, params)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"更新数据成功: 表={table}, 数据={data}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"更新数据失败: 表={table}, 数据={data}, 条件={condition}, 错误={str(e)}")
            raise
    
    def delete(self, table, condition, condition_params=None):
        """
        删除数据
        :param table: 表名
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # 构建SQL
                sql = f"DELETE FROM `{table}` WHERE {condition}"
                
                # 执行SQL
                if condition_params:
                    affected_rows = cursor.execute(sql, condition_params)
                else:
                    affected_rows = cursor.execute(sql)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"删除数据成功: 表={table}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"删除数据失败: 表={table}, 条件={condition}, 错误={str(e)}")
            raise
    
    def execute_transaction(self, sql_list, params_list=None):
        """
        执行事务
        :param sql_list: SQL语句列表
        :param params_list: SQL参数列表
        :return: 是否成功
        """
        # 确保连接已建立
        self.connect()
        
        # 开始事务
        try:
            with self.conn.cursor() as cursor:
                for i, sql in enumerate(sql_list):
                    # 获取对应的参数
                    params = None
                    if params_list and i < len(params_list):
                        params = params_list[i]
                    
                    # 执行SQL
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"执行事务成功: SQL条数={len(sql_list)}")
                
                return True
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"执行事务失败: 错误={str(e)}")
            raise


class PostgreSQLHandler:
    """
    PostgreSQL数据库操作工具类
    """

    def __init__(self, env="test"):
        """
        初始化数据库连接
        :param env: 环境名称，如test, dev, prod
        """
        # 加载数据库配置
        db_config = load_db_config()
        
        # 获取对应环境的数据库配置
        try:
            self.config = db_config["db_config"]["postgresql"][env]
        except KeyError:
            logger.error(f"找不到PostgreSQL数据库配置: env={env}")
            raise ValueError(f"找不到PostgreSQL数据库配置: env={env}")
        
        # 数据库连接
        self.conn = None
    
    def connect(self):
        """
        建立数据库连接
        :return: 数据库连接对象
        """
        if self.conn is None:
            try:
                # 延迟导入psycopg2，避免在未使用PostgreSQL时强制要求安装
                import psycopg2
                import psycopg2.extras
                
                self.conn = psycopg2.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    user=self.config["user"],
                    password=self.config["password"],
                    database=self.config["database"],
                    sslmode=self.config.get("sslmode", "prefer")
                )
                
                logger.info(f"PostgreSQL数据库连接成功: {self.config['host']}:{self.config['port']}/{self.config['database']}")
            except Exception as e:
                logger.error(f"PostgreSQL数据库连接失败: {str(e)}")
                raise
        
        return self.conn
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.info("PostgreSQL数据库连接已关闭")
    
    def execute_query(self, sql, params=None):
        """
        执行查询SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 查询结果
        """
        # 确保连接已建立
        self.connect()
        
        try:
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                result = cursor.fetchall()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"执行查询SQL成功: {sql}, 参数: {log_params}, 结果数: {len(result)}")
                
                return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"执行查询SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def execute_update(self, sql, params=None):
        """
        执行更新SQL
        :param sql: SQL语句
        :param params: SQL参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                affected_rows = cursor.rowcount
                self.conn.commit()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"执行更新SQL成功: {sql}, 参数: {log_params}, 影响行数: {affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            log_params = params if params else ""
            logger.error(f"执行更新SQL失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_one(self, sql, params=None):
        """
        查询单条记录
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单条记录
        """
        # 确保连接已建立
        self.connect()
        
        try:
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                result = cursor.fetchone()
                
                # 记录日志
                log_params = params if params else ""
                logger.info(f"查询单条记录成功: {sql}, 参数: {log_params}")
                
                return result
        except Exception as e:
            log_params = params if params else ""
            logger.error(f"查询单条记录失败: {sql}, 参数: {log_params}, 错误: {str(e)}")
            raise
    
    def fetch_value(self, sql, params=None):
        """
        查询单个值
        :param sql: SQL语句
        :param params: SQL参数
        :return: 单个值
        """
        # 查询单条记录
        record = self.fetch_one(sql, params)
        
        if record:
            # 获取第一个字段的值
            return list(record.values())[0]
        
        return None
    
    def insert(self, table, data):
        """
        插入数据
        :param table: 表名
        :param data: 数据字典
        :return: 自增ID
        """
        # 确保连接已建立
        self.connect()
        
        try:
            # 构建SQL
            columns = ", ".join(f'"{column}"' for column in data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            values = list(data.values())
            
            sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING id'
            
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, values)
                last_id = cursor.fetchone()['id']
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"插入数据成功: 表={table}, 数据={data}, ID={last_id}")
                
                return last_id
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"插入数据失败: 表={table}, 数据={data}, 错误={str(e)}")
            raise
    
    def update(self, table, data, condition, condition_params=None):
        """
        更新数据
        :param table: 表名
        :param data: 要更新的数据字典
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            # 构建SQL
            set_clause = ", ".join([f'"{column}" = %s' for column in data.keys()])
            values = list(data.values())
            
            sql = f'UPDATE "{table}" SET {set_clause} WHERE {condition}'
            
            # 合并参数
            if condition_params:
                if isinstance(condition_params, list):
                    params = values + condition_params
                else:
                    params = values + [condition_params]
            else:
                params = values
            
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
                affected_rows = cursor.rowcount
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"更新数据成功: 表={table}, 数据={data}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"更新数据失败: 表={table}, 数据={data}, 条件={condition}, 错误={str(e)}")
            raise
    
    def delete(self, table, condition, condition_params=None):
        """
        删除数据
        :param table: 表名
        :param condition: 条件语句
        :param condition_params: 条件参数
        :return: 影响行数
        """
        # 确保连接已建立
        self.connect()
        
        try:
            # 构建SQL
            sql = f'DELETE FROM "{table}" WHERE {condition}'
            
            with self.conn.cursor() as cursor:
                # 执行SQL
                if condition_params:
                    cursor.execute(sql, condition_params)
                else:
                    cursor.execute(sql)
                
                affected_rows = cursor.rowcount
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"删除数据成功: 表={table}, 条件={condition}, 影响行数={affected_rows}")
                
                return affected_rows
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"删除数据失败: 表={table}, 条件={condition}, 错误={str(e)}")
            raise
    
    def execute_transaction(self, sql_list, params_list=None):
        """
        执行事务
        :param sql_list: SQL语句列表
        :param params_list: SQL参数列表
        :return: 是否成功
        """
        # 确保连接已建立
        self.connect()
        
        # 开始事务
        try:
            with self.conn.cursor() as cursor:
                for i, sql in enumerate(sql_list):
                    # 获取对应的参数
                    params = None
                    if params_list and i < len(params_list):
                        params = params_list[i]
                    
                    # 执行SQL
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                
                # 提交事务
                self.conn.commit()
                
                logger.info(f"执行事务成功: SQL条数={len(sql_list)}")
                
                return True
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            
            logger.error(f"执行事务失败: 错误={str(e)}")
            raise 