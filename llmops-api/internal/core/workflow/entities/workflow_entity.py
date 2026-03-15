#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_entity
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
import re
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, root_validator

from internal.exception import ValidateErrorException
from .edge_entity import BaseEdgeData
from .node_entity import NodeResult, BaseNodeData, NodeType

# 工作流配置校验信息
WORKFLOW_CONFIG_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'
WORKFLOW_CONFIG_DESCRIPTION_MAX_LENGTH = 1024


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
    nodes: list[BaseNodeData] = Field(default_factory=list)  # 工作流节点信息列表
    edges: list[BaseEdgeData] = Field(default_factory=list)  # 工作流边信息列表

    @root_validator(pre=True)
    def validate_workflow_config(cls, values: dict[str, Any]):
        """自定义校验函数 校验工作流配置的所有参数"""

        # 校验工作流名称是否符合规则
        name = values.get("name", None)
        if not name or not re.match(WORKFLOW_CONFIG_NAME_PATTERN, name):
            raise ValidateErrorException("工作流名称仅支持字母、数字、下划线，且以字母、下划线为开头")
        # 校验工作流描述信息 文本需要传递到LLM 有长度显示
        description = values.get("description", None)
        if not description or len(description) > WORKFLOW_CONFIG_DESCRIPTION_MAX_LENGTH:
            raise ValidateErrorException("工作流描述信息长度不能超过1024个字符")

        # 获取 节点 边
        nodes = values.get("nodes", [])
        edges = values.get("edges", [])

        # 校验节点&边数据
        if not isinstance(nodes, list) or len(nodes) <= 0:
            raise ValidateErrorException("工作流节点列表信息错误")
        if not isinstance(edges, list) or len(edges) <= 0:
            raise ValidateErrorException("工作流边列表信息错误")

        # 节点数据模型类映射
        from internal.core.workflow.nodes import (
            CodeNodeData,
            DatasetRetrievalNodeData,
            EndNodeData,
            HttpRequestNodeData,
            LLMNodeData,
            StartNodeData,
            TemplateTransformNodeData,
            ToolNodeData,
        )
        node_data_classes = {
            NodeType.CODE: CodeNodeData,
            NodeType.DATASET_RETRIEVAL: DatasetRetrievalNodeData,
            NodeType.END: EndNodeData,
            NodeType.HTTP_REQUEST: HttpRequestNodeData,
            NodeType.LLM: LLMNodeData,
            NodeType.START: StartNodeData,
            NodeType.TEMPLATE_TRANSFORM: TemplateTransformNodeData,
            NodeType.TOOL: ToolNodeData,
        }

        # 处理节点数据
        start_nodes = 0
        end_nodes = 0
        node_data_dict: dict[UUID, BaseNodeData] = {}
        for node in nodes:
            # 校验每个节点数据是否为字典
            if not isinstance(node, dict):
                raise ValidateErrorException("工作流节点数据类型错误")
            # 校验每个节点节点类型是否存在
            node_type = node.get("node_type", "")
            node_data_cls = node_data_classes.get(node_type, None)
            if not node_data_cls:
                raise ValidateErrorException("工作流节点类型出错")

            # 实例化对应的节点数据 通过BaseModel校验
            node_data = node_data_cls(**node)

            # 校验是否有唯一的 开始&结束 节点
            if node_data.node_type == NodeType.START:
                if start_nodes >= 1:
                    raise ValidateErrorException("工作流只允许有一个开始节点")
                start_nodes += 1
            elif node_data.node_type == NodeType.END:
                if end_nodes >= 1:
                    raise ValidateErrorException("工作流只允许有一个结束节点")
                end_nodes += 1

            # 校验节点 ID&TITLE
            if node_data.id in node_data_dict:
                raise ValidateErrorException("每个节点的id必须唯一")
            if any(item.title.strip() == node_data.title.strip() for item in node_data_dict.values()):
                raise ValidateErrorException("每个节点的title必须唯一")
            # 添加数据到字典
            node_data_dict[node_data.id] = node_data

        # 处理边数据
        edge_data_dict: dict[UUID, BaseEdgeData] = {}
        for edge in edges:
            # 校验每边数据是否为字典
            if not isinstance(edge, dict):
                raise ValidateErrorException("工作流边数据类型错误")
            
            # 实例化边数据 通过BaseModel校验
            edge_data = BaseEdgeData(**edge)
            if edge_data.id in edge_data_dict:
                raise ValidateErrorException("每个边的id必须唯一")

            # 17.校验边的 source/target/source_type/target_type 是否在节点中存在
            if (
                    edge_data.source not in node_data_dict
                    or edge_data.source_type != node_data_dict[edge_data.source].node_type
                    or edge_data.target not in node_data_dict
                    or edge_data.target_type != node_data_dict[edge_data.target].node_type
            ):
                raise ValidateErrorException("工作流边起点/终点对应的节点不存在或类型错误")

            if any((item.source == edge_data.source and item.target == edge_data.target) for item in
                   edge_data_dict.values()):
                raise ValidateErrorException("工作流边数据不能重复")

            # 添加数据到字典
            edge_data_dict[edge_data.id] = edge_data

        values["nodes"] = list(node_data_dict.values())
        values["edges"] = list(edge_data_dict.values())

        return values


class WorkflowState(BaseModel):
    """工作流程序状态"""
    inputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输入
    outputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输出
    node_results: Annotated[list[NodeResult], _process_node_results]  # 各节点点的运行结果
