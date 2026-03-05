#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   llm_node
@Time   :   2026/3/5
@Author :   s.qiu@foxmail.com
"""
import time
from typing import Any

from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .llm_entity import LLMNodeData
from ...entities.node_entity import NodeResult, NodeStatus


class LLMNode(BaseNode):
    """语言模型节点"""
    node_data: LLMNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """语言模型节点 输入字段+预设Prompt生成对应内容后输出"""

        start_at = time.perf_counter()
        # 提取节点中输入的数据
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        # 格式化模板信息
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # 创建LLM实例 todo:多LLM待完善
        llm = ChatOpenAI(
            model=self.node_data.language_model_config.get("model", "gpt-4o-mini"),
            **self.node_data.language_model_config.get("parameters", {}),
        )
        content = ""
        for chunk in llm.stream(prompt_value):
            content += chunk.content

        # 提取构建输出数据
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs["output"] = content

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
