#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_tool_service
@Time   :   2025/12/1 14:04
@Author :   s.qiu@foxmail.com
"""
import mimetypes
import os
from dataclasses import dataclass

from flask import current_app
from injector import inject
from pydantic import BaseModel

from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具 服务"""
    builtin_tool_manager: BuiltinProviderManager
    builtin_category_manager: BuiltinCategoryManager

    def get_builtin_tools(self) -> list:
        """获取所有内置 供应商+工具信息 信息"""

        builtin_tools = []
        # 获取所有提供商
        providers = self.builtin_tool_manager.get_providers()

        # 遍历所有的提供商并提取工具信息
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {**provider_entity.model_dump(exclude=['icon']), 'tools': []}

            # 获取供应商下所有工具
            for tool_entity in provider.get_tool_entities():
                tool = provider.get_tool(tool_entity.name)

                tool_dict = {
                    **tool_entity.model_dump(),
                    'inputs': self.get_tool_inputs(tool)
                }
                builtin_tool["tools"].append(tool_dict)

            builtin_tools.append(builtin_tool)

        return builtin_tools

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据传递的 供应商+工具 名字获取指定工具信息"""

        # 获取内置的提供商
        provider = self.builtin_tool_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f'该供应商{provider_name}不存在')

        # 获取供应商下的工具实体
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f'该工具{tool_name}不存在')

        # 组装提供商和工具实体信息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)

        builtin_tool = {
            **tool_entity.model_dump(),
            'inputs': self.get_tool_inputs(tool),
            'created_at': provider_entity.created_at,
            'provider': {**provider_entity.model_dump(exclude=["icon", "created_at"])},
        }

        return builtin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """根据 供应商 获取该供应商图标 ion 流信息"""

        # 判断供应商是否存在
        provider = self.builtin_tool_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f'该供应商{provider_name}不存在')

        # 根据提供商名称确定图标文件夹路径
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))
        provider_path = os.path.join(root_path, 'internal', 'core', 'tools', 'builtin_tools', 'providers',
                                     provider_name)
        icon_path = os.path.join(provider_path, '_assets', provider.provider_entity.icon)

        # 检测icon是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"该供应商{provider_name}未提供图标")

        # 读取icon的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 7.读取icon的字节数据
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def get_categories(self) -> list:
        """获取所有内置插件的 分类信息"""
        category_map = self.builtin_category_manager.get_category_map()

        # 组装数据
        categories = []
        for category in category_map.values():
            categories.append({
                'name': category['entity'].name,
                'category': category['entity'].category,
                'icon': category['icon'],
            })

        return categories

    @classmethod
    def get_tool_inputs(cls, tool: str) -> list:
        """根据传入的工具获取inputs信息"""
        inputs = []

        if hasattr(tool, 'args_schema') and issubclass(tool.args_schema, BaseModel):
            for field_name, field_info in tool.args_schema.model_fields.items():
                inputs.append({
                    "name": field_name,
                    "description": field_info.description or "",
                    "required": field_info.is_required(),
                    "type": field_info.annotation.__name__,
                })

        return inputs
