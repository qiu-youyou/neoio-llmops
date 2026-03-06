#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from typing import Any, Optional

from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import PrivateAttr, BaseModel, Field, create_model

from .entities.node_entity import NodeType
from .entities.variable_entity import VARIABLE_TYPE_MAP
from .entities.workflow_entity import WorkflowConfig, WorkflowState
from .nodes import EndNode, StartNode, LLMNode, TemplateTransformNode


class Workflow(BaseTool):
    """工作流 Langchain 工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        """初始化 工作流配置 工作流图程序"""
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            args_schema=self._build_args_schema(workflow_config),
            **kwargs)

        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    @classmethod
    def _build_args_schema(cls, workflow_config: WorkflowConfig) -> type[BaseModel]:
        fields = {}
        inputs = next(
            (node.get("inputs", []) for node in workflow_config.nodes if node.get("node_type") == NodeType.START),
            []
        )

        for input in inputs:
            field_name = input.get("name")
            field_type = VARIABLE_TYPE_MAP.get(input.get("type"), str)
            field_required = input.get("required", True)
            field_description = input.get("description")

            if field_required:
                fields[field_name] = (field_type, Field(description=field_description))
            else:
                fields[field_name] = (Optional[field_type], Field(default=None, description=field_description))

        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        """构建工作流图程序"""
        graph = StateGraph(WorkflowState)
        # 提取nodes、edges信息
        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges

        # 遍历节点
        for node in nodes:
            node_flag = f"{node.get('node_type')}_{node.get('id')}"
            if node.get('node_type') == NodeType.START:
                graph.add_node(node_flag, StartNode(node_data=node))
            elif node.get('node_type') == NodeType.LLM:
                graph.add_node(node_flag, LLMNode(node_data=node))
            elif node.get('node_type') == NodeType.TEMPLATE_TRANSFORM:
                graph.add_node(node_flag, TemplateTransformNode(node_data=node))
            elif node.get('node_type') == NodeType.END:
                graph.add_node(node_flag, EndNode(node_data=node))

        # 遍历边
        for edge in edges:
            graph.add_edge(f"{edge.get('source_type')}_{edge.get('source')}",
                           f"{edge.get('target_type')}_{edge.get('target')}")

            if edge.get('source_type') == NodeType.START:
                start_node = f"{edge.get('source_type')}_{edge.get('source')}"
                graph.set_entry_point(start_node)

            if edge.get('target_type') == NodeType.END:
                end_node = f"{edge.get('target_type')}_{edge.get('target')}"
                graph.set_finish_point(end_node)

        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流基础 Run 方法"""
        return self._workflow.invoke({"inputs": kwargs})
