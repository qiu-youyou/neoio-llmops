#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_tool_handler
@Time   :   2025/12/1 13:51
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from injector import inject

from internal.service import BuiltinToolService
from pkg.response import success_message


@inject
@dataclass
class BuiltinToolHandler:
    """内置工具处理器"""
    builtin_tool_service: BuiltinToolService

    def get_builtin_tools(self):
        """获取所有内置 工具信息+供应商信息"""
        self.builtin_tool_service.get_builtin_tools()
        return success_message(f"应用创建成功, id 为")

    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据传递的 供应商+工具 名字获取指定工具信息"""
        pass
