#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_entity
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field

from .node_entity import NodeResult


def _process_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """工作流状态数据 归纳函数"""
    left = left or {}
    right = right or {}
    return {**left, **right}


def _process_node_results(left: list[NodeResult], right: list[NodeResult]) -> list[NodeResult]:
    """工作流状态节点结果 归纳函数"""
    left = left or []
    right = right or []
    return left + right


class WorkflowConfig(BaseModel):
    """工作流配置信息"""
    account_id: UUID
    name: str = ""  # 工作流名称
    description: str = ""  # 工作流描述
    nodes: list[Any] = Field(default_factory=list)  # 工作流节点信息列表
    edges: list[Any] = Field(default_factory=list)  # 工作流边信息列表


class WorkflowState(BaseModel):
    """工作流程序状态"""
    inputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输入
    outputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输出
    node_results: Annotated[list[NodeResult], _process_node_results]  # 各节点点的运行结果
