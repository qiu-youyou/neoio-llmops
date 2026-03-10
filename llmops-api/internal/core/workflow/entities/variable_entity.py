#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   variable_entity
@Time   :   2026/3/3
@Author :   s.qiu@foxmail.com
"""
import re
from enum import Enum
from typing import Union, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from internal.exception import ValidateErrorException


class VariableType(str, Enum):
    """变量类型 枚举"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"


# 变量类型与声明 映射
VARIABLE_TYPE_MAP = {
    VariableType.STRING: str,
    VariableType.INT: int,
    VariableType.FLOAT: float,
    VariableType.BOOLEAN: bool
}

# 变量类型映射 默认值
VARIABLE_TYPE_DEFAULT_VALUE_MAP = {
    VariableType.STRING: "",
    VariableType.INT: 0,
    VariableType.FLOAT: 0,
    VariableType.BOOLEAN: False,
}

# 变量名字正则匹配规则
VARIABLE_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'

# 描述最大长度
VARIABLE_DESCRIPTION_MAX_LENGTH = 1024


class VariableValueType(str, Enum):
    """变量内置类型 枚举"""
    REF = "ref"  # 引用类型
    LITERAL = "literal"  # 直接输入
    GENERATED = "generated"  # 生成的值


class VariableEntity(BaseModel):
    """变量实体"""

    class Value(BaseModel):
        """变量实体"""

        class Content(BaseModel):
            """变量内容实体 类型如果为引用 content记录节点ID+引用节点变量名称"""
            ref_node_id: UUID
            ref_var_name: str

        type: VariableValueType = VariableValueType.GENERATED
        content: Union[Content, str, int, float, bool] = ""

    name: str = ""  # 变量名
    description: str = ""  # 变量描述
    required: bool = True  # 是否必填
    type: VariableType = VariableType.STRING  # 变量类型
    value: Value = Field(default_factory=lambda: {"type": VariableValueType.LITERAL, "content": ""})  # 变量对应的值
    meta: dict[str, Any] = Field(default_factory=dict)  # 变量元数据，存储一些额外的信息

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        """自定义校验函数，用于校验变量名字"""
        if not re.match(VARIABLE_NAME_PATTERN, value):
            raise ValidateErrorException("变量名字仅支持字母、数字和下划线，且以字母/下划线为开头")
        return value

    @field_validator("description")
    def validate_description(cls, value: str) -> str:
        """自定义校验函数，用于校验描述信息，截取前1024个字符"""
        return value[:VARIABLE_DESCRIPTION_MAX_LENGTH]
