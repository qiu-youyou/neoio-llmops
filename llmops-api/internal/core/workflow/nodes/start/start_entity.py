#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   start_entity
@Time   :   2026/3/3
@Author :   s.qiu@foxmail.com
"""
from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """开始节点数据"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量
