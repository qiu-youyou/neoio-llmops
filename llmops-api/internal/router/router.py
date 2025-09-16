#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   router
@Time   :   2025/9/1 11:48
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handle import AppHandle


@inject
@dataclass
class Router:
    app_handle: AppHandle

    """路由"""

    def register_router(self, app: Flask):
        """注册路由"""
        # 创建一个蓝图
        bp = Blueprint('llmops', __name__, url_prefix='')

        # 将 URL 与对应的控制器方法绑定
        bp.add_url_rule(rule='/test', view_func=self.app_handle.test, methods=['POST'])

        bp.add_url_rule(rule='/app/completion', view_func=self.app_handle.completion, methods=['POST'])

        # 在应用上注册蓝图
        app.register_blueprint(bp)
