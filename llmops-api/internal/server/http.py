#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   http
@Time   :   2025/9/1 13:54
@Author :   s.qiu@foxmail.com
"""
import os

from flask import Flask

from config import Config
from internal.exception import CustomException
from internal.router import Router
from pkg.response import json, Response, fail_message


class Http(Flask):
    """HTTP 服务引擎"""

    def __init__(self, *args, conf: Config, router: Router, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化应用配置
        self.config.from_object(conf)

        # 异常错误处理自定义
        self.register_error_handler(Exception, self._register_error_handler)

        # 初始化扩展

        # 注册应用路由
        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        # 是否为抛出的 自定义异常
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {},
            ))

        # 如果开发环境抛出异常更详细的信息
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error

        # 生产环境返回 FAIL
        else:
            return fail_message(error.__str__())
