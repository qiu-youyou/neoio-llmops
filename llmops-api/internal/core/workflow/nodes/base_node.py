#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   base_node
@Time   :   2026/3/2
@Author :   s.qiu@foxmail.com
"""
from abc import ABC
from typing import Any

from langchain_core.runnables import RunnableSerializable

from internal.core.workflow.entities.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    """工作流节点基础类"""
    _node_data_cls: type[BaseNodeData]
    node_data: BaseNodeData

    def __init__(self, *args: Any, node_data: dict[str, Any], **kwargs):
        super().__init__(*args, node_data=self._node_data_cls(**node_data), **kwargs)
