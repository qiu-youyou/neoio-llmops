#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_tool_service
@Time   :   2025/12/1 14:04
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from injector import inject

from internal.core.tools.builtin_tools.providers.builtin_provider_manager import BuiltinProviderManager


@inject
@dataclass
class BuiltinToolService:
    """内置工具 服务"""
    builtin_tool_manager: BuiltinProviderManager

    def get_builtin_tools(self) -> list:
        """获取所有内置 供应商+工具信息 信息"""

        builtin_tools = []
        # 获取所有提供商
        providers = self.builtin_tool_manager.get_providers()
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {**provider_entity.model_dump(exclude=['icon']), 'tools': []}

            # 获取供应商下所有工具
            for tool_entity in provider.get_tool_entities():
                # tool = provider.get_tool(tool_entity.name)
                tool_dict = {**tool_entity.model_dump(), 'inputs': []}
                print(tool_dict)

        return builtin_tools

    def get_provider_tool(self, provider_name: str, tool_name: str):
        """根据传递的 供应商+工具 名字获取指定工具信息"""
        pass
