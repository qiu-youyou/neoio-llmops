#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   helper
@Time   :   2026/3/5 09:48
@Author :   s.qiu@foxmail.com
"""
from typing import Any

from internal.core.workflow.entities.variable_entity import VariableEntity, VARIABLE_TYPE_MAP, \
    VARIABLE_TYPE_DEFAULT_VALUE_MAP, VariableValueType
from internal.core.workflow.entities.workflow_entity import WorkflowState


def extract_variables_from_state(variables: list[VariableEntity], state: WorkflowState) -> dict[str, Any]:
    """从状态中提取变量映射"""
    variables_dict = {}

    # 遍历输入实体
    for variable in variables:
        variable_type_cls = VARIABLE_TYPE_MAP.get(variable.type)
        # 引用数据/输入数据 引用数据获取节点数据进行转换
        if variable.value.type == VariableValueType.LITERAL:
            variables_dict[variable.name] = variable_type_cls(variable.value.content)
        else:
            for node_result in state.node_results:
                if node_result.node_data.id == variable.value.content.ref_node_id:
                    variables_dict[variable.name] = variable_type_cls(node_result.outputs.get(
                        variable.value.content.ref_var_name, VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(variable.type)
                    ))
    return variables_dict
