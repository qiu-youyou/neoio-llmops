#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   end_entity
@Time   :   2026/3/3 14:36
@Author :   s.qiu@foxmail.com
"""
from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class EndNodeData(BaseNodeData):
    """结束节点数据"""
    outputs: list[VariableEntity] = Field(default_factory=list)  # 结束节点需要输出的数据
