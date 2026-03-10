#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   http_request_entity
@Time   :   2026/3/9
@Author :   s.qiu@foxmail.com
"""
from enum import Enum

from pydantic import HttpUrl, Field, field_validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.exception import ValidateErrorException


class HttpRequestMethod(str, Enum):
    """Http请求方法类型枚举"""
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"


class HttpRequestInputType(str, Enum):
    """Http请求输入变量类型"""
    PARAMS = "params"  # query参数
    HEADERS = "headers"  # header请求头
    BODY = "body"  # body参数


class HttpRequestNodeData(BaseNodeData):
    """HTTP请求节点数据"""
    url: HttpUrl = ""  # 请求URL地址
    method: HttpRequestMethod = HttpRequestMethod.GET  # API请求方法
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量列表
    outputs: list[VariableEntity] = Field(
        exclude=True,
        default_factory=lambda: [
            VariableEntity(
                name="status_code",
                type=VariableType.INT,
                value={"type": VariableValueType.GENERATED, "content": 0},
            ),
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED}),
        ],
    )

    @field_validator("inputs")
    def validate_inputs(cls, inputs: list[VariableEntity]):
        """校验输入列表"""
        for input in inputs:
            if input.meta.get("type") not in HttpRequestInputType.__members__.values():
                raise ValidateErrorException("Http请求参数结构错误")
        return inputs
