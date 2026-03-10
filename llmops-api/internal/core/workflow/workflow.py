#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from typing import Any, Optional

from flask import current_app
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import PrivateAttr, BaseModel, Field, create_model

from internal.exception import ValidateErrorException
from .entities.node_entity import NodeType
from .entities.variable_entity import VARIABLE_TYPE_MAP
from .entities.workflow_entity import WorkflowConfig, WorkflowState
from .nodes import StartNode, EndNode, DatasetRetrievalNode, LLMNode, TemplateTransformNode, CodeNode, ToolNode, \
    HttpRequestNode

NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.TEMPLATE_TRANSFORM: TemplateTransformNode,
    NodeType.DATASET_RETRIEVAL: DatasetRetrievalNode,
    NodeType.HTTP_REQUEST: HttpRequestNode,
    NodeType.CODE: CodeNode,
    NodeType.TOOL: ToolNode,
}


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
            if node.get("node_type") in NodeClasses.keys():
                if node.get("node_type") == NodeType.DATASET_RETRIEVAL:
                    graph.add_node(node_flag, NodeClasses[node.get("node_type")](
                        flask_app=current_app._get_current_object(),
                        account_id=self._workflow_config.account_id,
                        node_data=node))
                else:
                    graph.add_node(node_flag, NodeClasses[node.get("node_type")](node_data=node))
            else:
                raise ValidateErrorException("工作流节点类型不存在！")

        # 遍历边
        parallel_edges = {}  # key:终点，value:起点列表
        start_node = ""
        end_node = ""
        for edge in edges:
            source_node = f"{edge.get('source_type')}_{edge.get('source')}"
            target_node = f"{edge.get('target_type')}_{edge.get('target')}"

            if target_node not in parallel_edges:
                parallel_edges[target_node] = [source_node]
            else:
                parallel_edges[target_node].append(source_node)

            # 开始节点、结束节点
            if edge.get('source_type') == NodeType.START:
                start_node = f"{edge.get('source_type')}_{edge.get('source')}"
            if edge.get('target_type') == NodeType.END:
                end_node = f"{edge.get('target_type')}_{edge.get('target')}"

        graph.set_entry_point(start_node)
        graph.set_finish_point(end_node)

        # 遍历合并边
        for target_node, source_nodes in parallel_edges.items():
            graph.add_edge(source_nodes, target_node)

        workflow = graph.compile()
        # image_data = workflow.get_graph().draw_mermaid_png()
        # with open("workflow.png", "wb") as f:
        #     f.write(image_data)

        return workflow

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流基础 Run 方法"""
        return self._workflow.invoke({"inputs": kwargs})
