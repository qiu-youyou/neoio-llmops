#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   tool_entity
@Time   :   2026/3/9
@Author :   s.qiu@foxmail.com
"""
from typing import Literal, Any

from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType


class ToolNodeData(BaseNodeData):
    """工具节点 数据"""
    tool_type: Literal["builtin_tool", "api_tool"] = Field(alias="type")  # 工具类型
    provider_id: str  # 工具提供者id
    tool_id: str  # 工具id
    params: dict[str, Any] = Field(default_factory=dict)  # 内置工具设置参数
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量列表
    outputs: list[VariableEntity] = Field(exclude=True, default_factory=lambda: [  # 输出变量列表
        VariableEntity(name="text", value={"type": VariableValueType.GENERATED})
    ])
