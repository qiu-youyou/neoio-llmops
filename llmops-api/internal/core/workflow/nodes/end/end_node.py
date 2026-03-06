#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   end_node
@Time   :   2026/3/3
@Author :   s.qiu@foxmail.com
"""
from typing import Any

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VariableValueType, VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from .end_entity import EndNodeData


class EndNode(BaseNode):
    """结束节点"""
    node_data: EndNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """结束节点函数 提取状态数据更新OUTPUTS"""
        outputs = self.node_data.outputs
        outputs_dict = {}
        # 遍历需要输出的数据 并判断字段是引用还是直接输入
        for output in outputs:
            if output.value.type == VariableValueType.LITERAL:
                outputs_dict[output.name] = output.value.content
            else:
                for node_result in state.node_results:
                    if node_result.node_data.id == output.value.content.ref_node_id:
                        outputs_dict[output.name] = node_result.outputs.get(
                            output.value.content.ref_var_name,
                            VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(output.type)
                        )
        # 组装状态返回
        return {
            "outputs": outputs_dict,
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs={},
                    outputs=outputs_dict
                )
            ]
        }
