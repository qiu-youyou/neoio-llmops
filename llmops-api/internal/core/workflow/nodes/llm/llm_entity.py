#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   llm-entity
@Time   :   2026/3/4
@Author :   s.qiu@foxmail.com
"""
from typing import Any

from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType
from internal.entity.app_entity import DEFAULT_APP_CONFIG


class LLMNodeData(BaseNodeData):
    """大语言模型节点数据"""
    prompt: str  # 提示词
    language_model_config: dict[str, Any] = Field(  # 大模型配置信息
        alias="model_config",
        default_factory=lambda: DEFAULT_APP_CONFIG["model_config"],
    )
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入信息列表
    outputs: list[VariableEntity] = Field(  # 输出信息列表
        exclude=True,
        default_factory=lambda: [VariableEntity(name="output", value={"type": VariableValueType.GENERATED})]
    )
