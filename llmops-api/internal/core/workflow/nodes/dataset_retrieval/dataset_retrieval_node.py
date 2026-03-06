#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_retrieval_node
@Time   :   2026/3/5
@Author :   s.qiu@foxmail.com
"""
import time
from typing import Any
from uuid import UUID

from flask import Flask
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .dataset_retrieval_entity import DatasetRetrievalNodeData


class DatasetRetrievalNode(BaseNode):
    """知识库检索 节点"""
    node_data: DatasetRetrievalNodeData
    _retrieval_tool: BaseTool = PrivateAttr(None)

    def __init__(self, *args: Any, flask_app: Flask, account_id: UUID, **kwargs: Any):
        """构造函数 知识库节点初始化"""
        super().__init__(*args, **kwargs)
        # 构建检索服务工具
        from app.http.module import injector
        from internal.service import RetrievalService
        retrieval_service = injector.get(RetrievalService)
        self._retrieval_tool = retrieval_service.create_langchain_tool_from_search(
            flask_app=flask_app,
            dataset_ids=self.node_data.dataset_ids,
            account_id=account_id,
            **self.node_data.retrieval_config.model_dump(),
        )

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """知识库检索节点"""
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        # 调用知识库检索工具
        combine_documents = self._retrieval_tool.invoke(inputs_dict)
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = combine_documents
        else:
            outputs["combine_documents"] = combine_documents
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at)
                )
            ]
        }
