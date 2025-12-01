#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   provider_entity
@Time   :   2025/11/27 11:38
@Author :   s.qiu@foxmail.com
"""
import os
from typing import Any

import yaml
from pydantic import BaseModel, Field

from internal.lib import dynamic_import
from .tool_entity import ToolEntity


class ProviderEntity(BaseModel):
    """服务提供商实体 映射的数据是 providers.yaml"""
    name: str  # 名称
    label: str  # 标签
    description: str  # 描述
    icon: str  # 图标
    background: str  # 背景色
    category: str  # 分类信息


class Provider(BaseModel):
    """服务提供商，在该类下 可以获取该服务提供商的所有工具、描述、标签等所有信息"""

    name: str  # 服务提供商名字
    position: int  # 服务提供商的顺序
    provider_entity: ProviderEntity  # 服务提供商实体
    tool_entity_map: dict[str, ToolEntity] = Field(default_factory=dict)  # 工具实体
    tool_func_map: dict[str, Any] = Field(default_factory=dict)  # 工具函数映射表

    def __init__(self, **kwargs):
        """对应服务提供商初始化"""
        super().__init__(**kwargs)
        self._provider_init()

    def get_tool(self, tool_name: str) -> Any:
        """根据工具名称 获取该提供商下的指定工具"""
        return self.tool_func_map.get(tool_name)

    def get_tool_entity(self, tool_name: str) -> Any:
        """根据工具名称 获取该提供商下的指定工具的信息实体"""
        return self.tool_entity_map.get(tool_name)

    def get_tool_entities(self) -> list[ToolEntity]:
        """获取该服务提供商下的 所有工具信息实体 立标"""
        return list(self.tool_entity_map.values())

    def _provider_init(self):
        """服务提供商初始化函数"""

        # 当前类的路径 计算到服务商提供的地址
        current_path = os.path.abspath(__file__)
        entities_path = os.path.dirname(current_path)
        providers_path = os.path.join(os.path.dirname(entities_path), "providers")
        providers_tool_path = os.path.join(providers_path, self.name)

        # 组装获取 positions.yaml 数据
        position_yaml_path = os.path.join(providers_tool_path, "positions.yaml")
        with open(position_yaml_path, encoding="utf-8") as f:
            position_yaml_data = yaml.safe_load(f)

        # 循环获取服务提供商的位置信息获取提供上的工具名字
        for tool_name in position_yaml_data:
            tool_yaml_path = os.path.join(providers_tool_path, f"{tool_name}.yaml")
            with open(tool_yaml_path, encoding="utf-8") as f:
                tool_yaml_data = yaml.safe_load(f)

            # 工具信息实体填充到 tool_entity_map
            self.tool_entity_map[tool_name] = ToolEntity(**tool_yaml_data)
            # 动态导入对应的工具填充到 tool_func_map
            self.tool_func_map[tool_name] = dynamic_import(
                f"internal.core.tools.builtin_tools.providers.{self.name}",
                tool_name
            )
