#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_entity
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
import re
from collections import defaultdict, deque
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, root_validator

from internal.exception import ValidateErrorException
from .edge_entity import BaseEdgeData
from .node_entity import NodeResult, BaseNodeData, NodeType
from .variable_entity import VariableEntity, VariableValueType

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

        # 构建邻接表、逆邻接表、入度以及出度
        adj_list = cls._build_adj_list(edge_data_dict.values())
        reverse_adj_list = cls._build_reverse_adj_list(edge_data_dict.values())
        in_degree, out_degree = cls._build_in_degree_and_out_degree(edge_data_dict.values())

        # 从边的关系中校验是否有唯一的开始/结束节点
        # 入度为0就是开始节点 出度为0就是结束节点
        start_nodes = [node_data for node_data in node_data_dict.values() if in_degree[node_data.id] == 0]
        end_nodes = [node_data for node_data in node_data_dict.values() if out_degree[node_data.id] == 0]
        if (len(start_nodes) != 1
                or len(end_nodes) != 1
                or start_nodes[0].node_type != NodeType.START
                or end_nodes[0].node_type != NodeType.END):
            raise ValidateErrorException("工作流中有切只有一个开始/结束节点")

        # 校验图的连通性 无孤立节点、无循环边结构
        start_node_data = start_nodes[0]
        if not cls._is_connect(adj_list, start_node_data.id):
            raise ValidateErrorException("工作流中存在孤立节点")

        # 校验边中是否存在环路-循环边
        if cls._is_cycle(node_data_dict.values(), adj_list, in_degree):
            raise ValidateErrorException("工作流中存在环路")

        # 校验 nodes、edges 中 数据应用是否正确 inputs/outputs
        cls._validate_inputs_ref(node_data_dict, reverse_adj_list)

        values["nodes"] = list(node_data_dict.values())
        values["edges"] = list(edge_data_dict.values())

        return values

    @classmethod
    def _is_cycle(cls, nodes: list[BaseNodeData], adj_list: defaultdict[Any, list],
                  in_degree: defaultdict[Any, list]) -> bool:
        """拓扑排序 Kahn算法 检测图中是否存在环路:
        Kahn 算法的核心为：如果存在环，那么至少有一个非结束节点的入度大于等于2，并且该入度无法消减到0，
        这就会导致该节点后续的所有子节点在该算法下都无法浏览 那么访问次数肯定 小于总节点数"""
        # 存储所有入度为0的开始节点
        zero_in_degree_nodes = deque([node.id for node in nodes if in_degree[node.id] == 0])
        # 记录已经访问的节点数量
        visited_count = 0
        # 遍历入度为0的节点信息
        while zero_in_degree_nodes:
            node_id = zero_in_degree_nodes.popleft()
            visited_count += 1
            # 遍历获取到的节点的子节点
            for neighbor in adj_list[node_id]:
                # 将子节点的入度-1 如果为0 则添加到队列中
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    zero_in_degree_nodes.append(neighbor)
        # 访问次数与总节点数如果不相等或小于总节点 则存在环
        return visited_count != len(nodes)

    @classmethod
    def _is_connect(cls, adj_list: defaultdict[Any, list], start_node_id: UUID) -> bool:
        """BFS广度优先搜索遍历检查图是否流通"""
        # 记录已经访问的节点
        visited = set()
        # 双向队列 记录开始访问节点对应ID
        queue = deque([start_node_id])
        visited.add(start_node_id)
        # 遍历队列 广度优先搜索节点对应子节点
        while queue:
            node_id = queue.popleft()
            for neighbor in adj_list[node_id]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        # 已访问节点数量是否和总节点数量相等 不相等则存在孤立节点
        return len(visited) == len(adj_list)

    @classmethod
    def _validate_inputs_ref(
            cls,
            node_data_dict: dict[UUID, BaseNodeData],
            reverse_adj_list: defaultdict[Any, list],
    ) -> None:
        """校入数据引用是否正确"""
        # 循环遍历所有节点数据逐个处理
        for node_data in node_data_dict.values():
            # 提取该节点的所有前置节点
            predecessors = cls._get_predecessors(reverse_adj_list, node_data.id)

            # 如果节点数据类型不是START则校验输入数据引用（因为开始节点不需要校验）
            if node_data.node_type != NodeType.START:
                # 根据节点类型从inputs或者是outputs中提取需要校验的数据
                variables: list[VariableEntity] = (
                    node_data.inputs if node_data.node_type != NodeType.END
                    else node_data.outputs
                )

                # 循环遍历所有需要校验的变量信息
                for variable in variables:
                    # 如果变量类型为引用，则需要校验
                    if variable.value.type == VariableValueType.REF:
                        # 判断前置节点是否为空，或者引用id不在前置节点内，则直接抛出错误
                        if (len(predecessors) <= 0
                                or variable.value.content.ref_node_id not in predecessors):
                            raise ValidateErrorException(f"工作流节点[{node_data.title}]引用数据出错")

                        # 提取数据引用的前置节点数据
                        ref_node_data = node_data_dict.get(variable.value.content.ref_node_id)

                        # 获取引用变量列表，如果是开始节点则从inputs中获取数据，否则从outputs中获取数据
                        ref_variables = (
                            ref_node_data.inputs if ref_node_data.node_type == NodeType.START
                            else ref_node_data.outputs
                        )

                        # 判断引用变量列表中是否存在该引用名字
                        if not any([ref_variable.name == variable.value.content.ref_var_name] for ref_variable in
                                   ref_variables):
                            raise ValidateErrorException(
                                f"工作流节点[{node_data.title}]引用了不存在的节点变量")

    @classmethod
    def _build_adj_list(cls, edges: list[BaseEdgeData]) -> defaultdict[Any, list]:
        """构建邻接表 节点ID: 后继节点"""
        adj_list = defaultdict(list)
        for edge in edges:
            adj_list[edge.source].append(edge.target)
        return adj_list

    @classmethod
    def _build_reverse_adj_list(cls, edges: list[BaseEdgeData]) -> defaultdict[Any, list]:
        """构建逆邻接表 节点ID：节点直接父节点"""
        reverse_adj_list = defaultdict(list)
        for edge in edges:
            reverse_adj_list[edge.target].append(edge.source)
        return reverse_adj_list

    @classmethod
    def _build_degrees(cls, edges: list[BaseEdgeData]) -> tuple[defaultdict[Any, int], defaultdict[Any, int]]:
        """计算每个节点的 in_degress&out_degrees 入度和出度"""
        in_degree = defaultdict(list)
        out_degree = defaultdict(list)
        for edge in edges:
            in_degree[edge.target] += 1
            out_degree[edge.source] += 1
        return in_degree, out_degree

    @classmethod
    def _get_predecessors(cls, reverse_adj_list: defaultdict[Any, list], target_node_id: UUID) -> list[UUID]:
        """获取某个几点的所有前置节点 根据逆邻接表&目标节点"""
        visited = set()
        predecessors = []

        def dfs(node_id: UUID):
            """广度搜索优先遍历所有前置节点"""
            if node_id not in visited:
                visited.add(node_id)
                predecessors.append(node_id)
                for neighbor in reverse_adj_list[node_id]:
                    dfs(neighbor)

        dfs(target_node_id)
        return predecessors


class WorkflowState(BaseModel):
    """工作流程序状态"""
    inputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输入
    outputs: Annotated[dict[str, Any], _process_dict]  # 工作流状态输出
    node_results: Annotated[list[NodeResult], _process_node_results]  # 各节点点的运行结果
