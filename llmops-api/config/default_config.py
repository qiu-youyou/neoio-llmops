#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   default_config.py
@Time   :   2025/9/9 16:52
@Author :   s.qiu@foxmail.com
"""

DEFAULT_CONFIG = {
    # wft 默认配置
    "WTF_CSRF_ENABLED": "False",

    # SQLALchemy 默认配置
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",
}
