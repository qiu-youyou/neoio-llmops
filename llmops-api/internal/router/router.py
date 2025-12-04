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

from internal.handle import AppHandle, BuiltinToolHandler


@inject
@dataclass
class Router:
    app_handle: AppHandle
    builtin_tool_handler: BuiltinToolHandler

    """路由"""

    def register_router(self, app: Flask):
        """注册路由"""
        # 创建一个蓝图
        bp = Blueprint('llmops', __name__, url_prefix='')

        # 将 URL 与对应的控制器方法绑定
        bp.add_url_rule(rule='/test', view_func=self.app_handle.test, methods=['POST'])

        bp.add_url_rule(rule='/app/<uuid:app_id>/debug', view_func=self.app_handle.debug, methods=['POST'])

        # app 增删改查
        bp.add_url_rule(rule='/app', view_func=self.app_handle.create_app, methods=['POST'])
        bp.add_url_rule(rule='/app/<uuid:id>', view_func=self.app_handle.get_app)
        bp.add_url_rule(rule='/app/<uuid:id>', view_func=self.app_handle.update_app, methods=['POST'])
        bp.add_url_rule(rule='/app/<uuid:id>/delete', view_func=self.app_handle.delete_app, methods=['POST'])

        # 内置插件广场 模块
        bp.add_url_rule(rule='/builtin_tools', view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            view_func=self.builtin_tool_handler.get_provider_tool,
        )
        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon,
        )
        bp.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_categories,
        )

        # 自定义插件广场 模块
        
        # 在应用上注册蓝图
        app.register_blueprint(bp)
