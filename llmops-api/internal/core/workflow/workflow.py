#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from typing import Any, Iterator

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import PrivateAttr

from .entities.workflow_entity import WorkflowConfig, WorkflowState


class Workflow(BaseTool):
    """工作流 Langchain 工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        """初始化 工作流配置 工作流图程序"""
        super().__init__(name=workflow_config.name, description=workflow_config.description, **kwargs)

        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """构建工作流图程序"""
        graph = StateGraph(WorkflowState)

        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流基础 Run 方法"""
        return self._workflow.invoke({"inputs": kwargs})

    def stream(
            self,
            input: Input,
            config: RunnableConfig | None = None,
            **kwargs: Any | None,
    ) -> Iterator[Output]:
        """工作流流式输出每个节点的结果"""
        return self._workflow.stream({"inputs": input})
