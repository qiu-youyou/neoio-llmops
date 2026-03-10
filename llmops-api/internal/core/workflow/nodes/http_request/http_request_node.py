#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   http_request_node
@Time   :   2026/3/9
@Author :   s.qiu@foxmail.com
"""
import time
from typing import Any

import requests
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .http_request_entity import HttpRequestNodeData, HttpRequestInputType, HttpRequestMethod


class HttpRequestNode(BaseNode):
    """HTTP节点"""
    node_data: HttpRequestNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """HTTP节点调用函数 指定URL发起请求获取响应"""
        start_at = time.perf_counter()
        _inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        inputs_dict = {
            HttpRequestInputType.PARAMS: {},
            HttpRequestInputType.HEADERS: {},
            HttpRequestInputType.BODY: {}
        }
        for input in self.node_data.inputs:
            inputs_dict[input.meta.get("type")][input.name] = _inputs_dict.get(input.name)

        # 请求方法映射
        request_methods = {
            HttpRequestMethod.GET: requests.get,
            HttpRequestMethod.POST: requests.post,
            HttpRequestMethod.PUT: requests.put,
            HttpRequestMethod.PATCH: requests.patch,
            HttpRequestMethod.DELETE: requests.delete,
            HttpRequestMethod.HEAD: requests.head,
            HttpRequestMethod.OPTIONS: requests.options,
        }

        # 发起请求
        request_method = request_methods[self.node_data.method]
        if self.node_data.method == HttpRequestMethod.GET:
            response = request_method(
                self.node_data.url,
                headers=inputs_dict[HttpRequestInputType.HEADERS],
                params=inputs_dict[HttpRequestInputType.PARAMS]
            )
        else:
            response = request_method(
                self.node_data.url,
                headers=inputs_dict[HttpRequestInputType.HEADERS],
                params=inputs_dict[HttpRequestInputType.PARAMS],
                data=inputs_dict[HttpRequestInputType.BODY]
            )

        # 构建输出数据结构
        text = response.text
        status_code = response.status_code
        outputs = {"text": text, "status_code": status_code}
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
