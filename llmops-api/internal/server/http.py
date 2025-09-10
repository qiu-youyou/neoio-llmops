#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   http
@Time   :   2025/9/1 13:54
@Author :   s.qiu@foxmail.com
"""

from flask import Flask

from config import Config
from internal.router import Router


class Http(Flask):
    """HTTP 服务引擎"""

    def __init__(self, *args, conf: Config, router: Router, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化应用配置
        self.config.from_object(conf)
        
        # 注册应用路由
        router.register_router(self)
