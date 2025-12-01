#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   provider_factory
@Time   :   2025/11/27 11:06
@Author :   s.qiu@foxmail.com
"""
import os
from typing import Any

import yaml
from injector import inject, singleton

from internal.core.tools.builtin_tools.entity import (
    ProviderEntity, Provider
)


@inject
@singleton
class BuiltinProviderManager:
    """服务提供商工厂类"""
    provider_map: dict[str, Provider] = {}

    def __init__(self):
        """初始化对应的 provider_tool_map"""
        self._get_provider_tool_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据名称获取 服务提供商"""
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        """获取所有的 服务提供商"""
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        """获取所有服务提供商 实体信息列表"""
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str) -> Any:
        """根据提供商+工具名称 获取指定的工具实体信息"""
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.get_tool(tool_name)

    def _get_provider_tool_map(self):
        """项目初始化时获取服务提供商、工具的映射关系并填充provider_tool_map"""
        if self.provider_map:
            return

        # 获取当前类所在文件路径
        current_path = os.path.abspath(__file__)
        providers_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        # 读取 providers.yaml
        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity,
            )
