#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   redis_extension
@Time   :   2025/12/17 14:05
@Author :   s.qiu@foxmail.com
"""
import redis
from flask import Flask
from redis.connection import Connection, SSLConnection

redis_client = redis.Redis()


def init_app(app: Flask):
    """初始化 redis 客户端"""

    # 不同场景使用不同连接方式
    connection_class = Connection
    if app.config.get("REDIS_USE_SSL"):
        connection_class = SSLConnection

    # 创建连接池
    redis_client.connection_class = redis.ConnectionPool(**{
        "host": app.config.get("REDIS_HOST", "localhost"),
        "port": app.config.get("REDIS_PORT", "6379"),
        "username": app.config.get("REDIS_USERNAME", None),
        "password": app.config.get("REDIS_PASSWORD", None),
        "db": app.config.get("REDIS_DB", 0),
        "encoding": "utf-8",
        "encoding_errors": "strict",
        "decode_responses": False,
    }, connection_class=connection_class)
    app.extensions["redis"] = redis_client
