#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   code_node
@Time   :   2026/3/6
@Author :   s.qiu@foxmail.com
"""

import ast
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.exception import FailException
from .code_entity import CodeNodeData


class CodeNode(BaseNode):
    """代码运行节点"""
    node_data: CodeNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """Python代码运行节点 执行代码函数名字必须为main，参数名为params,只有一个参数 不允许有额外的语句"""
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 执行代码 todo:待完善沙箱或容器中执行
        result = self._execute_function(self.node_data.code, params=inputs_dict)
        if not isinstance(result, dict):
            raise FailException("main函数的返回值必须是一个字典")

        # 提取数据组装
        outputs_dict = {}
        outputs = self.node_data.outputs
        for output in outputs:
            outputs_dict[output.name] = result.get(output.name, VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(output.type))
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs_dict,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }

    @classmethod
    def _execute_function(cls, code: str, *args, **kwargs):
        """执行python函数"""
        try:
            # 解析代码为AST
            tree = ast.parse(code)
            main_func = None

            # 检查函数名是否为 main，参数为 params
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name == "main":
                        if main_func:
                            raise FailException("代码中只能有一个main函数")
                        if len(node.args.args) != 1 or node.args.args[0].arg != "params":
                            raise FailException("main函数必须只有一个参数，且参数为params")
                        main_func = node
                    else:
                        raise FailException("代码中不允许包含其他函数，只允许有一个main函数")
                else:
                    raise FailException("代码中只能包含函数定义，不允许其他语句存在")
            if not main_func:
                raise FailException("代码中必须包含名为main的函数")

            # 代码通过校验后执行代码
            local_vars = {}
            exec(code, {}, local_vars)
            if "main" in local_vars and callable(local_vars["main"]):
                return local_vars["main"](*args, **kwargs)
            else:
                raise FailException("main函数必须是磕调用函数")
        except Exception as e:
            raise FailException("Python代码执行错误")
