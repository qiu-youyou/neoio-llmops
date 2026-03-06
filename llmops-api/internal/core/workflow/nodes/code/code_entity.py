#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   code_entity
@Time   :   2026/3/6
@Author :   s.qiu@foxmail.com
"""
from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity

# 默认代码
DEFAULT_CODE = """
def main(params):
    return params
"""


class CodeNodeData(BaseNodeData):
    """PYTHON 代码节点数据"""
    code: str = DEFAULT_CODE  # python 代码
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入列表
    outputs: list[VariableEntity] = Field(default_factory=list)  # 输出列表
