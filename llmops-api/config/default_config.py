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

    # Redis 默认配置
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_USERNAME": "",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0",
    "REDIS_USE_SSL": "False",

    # Celery默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_BACKEND_DB": 1,
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 3600,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",
}
