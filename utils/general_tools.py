#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from utils.logger import logger
from utils.data_handler import load_config

def find_user_by_description_pattern(pattern):
    """
    根据描述模式查找匹配的用户
    :param pattern: 描述中应包含的正则表达式模式
    :return: (用户ID, 用户描述) 或 (None, None)
    """
    users_config = load_config("users.yaml")
    for user_id, config in users_config.items():
        description = config.get("description", "")
        if re.search(pattern, description, re.IGNORECASE):
            logger.info(f"找到匹配描述的用户: {user_id}, 描述: {description}")
            return user_id, description
    
    logger.warning(f"未找到匹配描述的用户: {pattern}")
    return None, None
