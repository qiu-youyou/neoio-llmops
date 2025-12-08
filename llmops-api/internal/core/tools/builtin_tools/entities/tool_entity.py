#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   tool_entity
@Time   :   2025/11/27 11:49
@Author :   s.qiu@foxmail.com
"""

from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class ToolParamsType(str, Enum):
    """工具参数类型 枚举类"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"


class ToolParam(BaseModel):
    """工具参数类型"""
    name: str  # 实际名称
    label: str  # 展示标签
    type: ToolParamsType  # 参数类型
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 参数默认值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    options: list[dict[str, Any]] = Field(default_factory=list)  # 选项数据源


class ToolEntity(BaseModel):
    """工具实体类 存储的信息映射的是 工具名.yaml 的数据"""
    name: str  # 工具名称
    label: str  # 工具标签
    description: str  # 工具的描述
    params: list[ToolParam] = Field(default_factory=list)  # 工具的参数
