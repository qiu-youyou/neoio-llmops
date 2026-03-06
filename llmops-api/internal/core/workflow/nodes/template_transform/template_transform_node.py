#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   template_transform_node
@Time   :   2026/3/5
@Author :   s.qiu@foxmail.com
"""
import time
from typing import Any

from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeStatus, NodeResult
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from .template_transform_entity import TemplateTransformNodeData
from ...utils.helper import extract_variables_from_state


class TemplateTransformNode(BaseNode):
    """模版转换节点 多个变量合并为一个"""
    node_data: TemplateTransformNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:x
        """模板转换节点 执行函数"""
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        # 格式化模板信息
        template = Template(self.node_data.template)
        template_value = template.render(**inputs_dict)

        outputs = {"output": template_value}

        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
