#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import PrivateAttr

from .entities.node_entity import NodeType
from .entities.workflow_entity import WorkflowConfig, WorkflowState
from .nodes import EndNode


class Workflow(BaseTool):
    """工作流 Langchain 工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        """初始化 工作流配置 工作流图程序"""
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            **kwargs)

        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

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
                pass
            elif node.get('node_type') == NodeType.END:
                graph.add_node(node_flag, EndNode(node_data=node))

        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流基础 Run 方法"""
        return self._workflow.invoke({"inputs": kwargs})
