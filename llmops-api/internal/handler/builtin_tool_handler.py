#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_tool_handler
@Time   :   2025/12/1 13:51
@Author :   s.qiu@foxmail.com
"""

import io
from dataclasses import dataclass

from flask import send_file
from flask_login import login_required
from injector import inject

from internal.service import BuiltinToolService
from pkg.response import success_json


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理器"""
    builtin_tool_service: BuiltinToolService

    @login_required
    def get_builtin_tools(self):
        """获取所有内置插件的 供应商信息+工具信息"""
        builtin_tools = self.builtin_tool_service.get_builtin_tools()
        return success_json(builtin_tools)

    @login_required
    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据传递的 供应商+工具 名字获取指定的内置工具信息"""
        builtin_tool = self.builtin_tool_service.get_provider_tool(provider_name, tool_name)
        return success_json(builtin_tool)

    @login_required
    def get_provider_icon(self, provider_name: str):
        """根据 供应商 获取该供应商图标"""
        icon, mimetype = self.builtin_tool_service.get_provider_icon(provider_name)
        return send_file(io.BytesIO(icon), mimetype)

    @login_required
    def get_categories(self):
        """获取内置插件的分类信息列表"""
        categories = self.builtin_tool_service.get_categories()
        return success_json(categories)
