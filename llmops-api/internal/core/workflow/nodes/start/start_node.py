#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   start_node
@Time   :   2026/3/3
@Author :   s.qiu@foxmail.com
"""
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.exception import FailException
from .start_entity import StartNodeData


class StartNode(BaseNode):
    """开始节点"""
    node_data: StartNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """开始节点函数 提取状态输入生成节点结果"""

        start_at = time.perf_counter()
        inputs = self.node_data.inputs
        # 提取并校验输入中的数据
        outputs_dict = {}
        for input in inputs:

            input_value = state.inputs.get(input.name, None)
            if input_value is None:
                if input.required:
                    raise FailException(f"工作流参数错误，{input.type}为必填参数")
                else:
                    input_value = VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(input.type)
            outputs_dict[input.name] = input_value

        return {"node_results": [NodeResult(
            node_data=self.node_data,
            status=NodeStatus.SUCCEEDED,
            inputs=state.inputs,
            outputs=outputs_dict,
            latency=(time.perf_counter() - start_at)
        )]}
