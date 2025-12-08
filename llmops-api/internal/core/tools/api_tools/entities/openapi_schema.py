#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   openapi_schema
@Time   :   2025/12/8 11:34
@Author :   s.qiu@foxmail.com
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from internal.exception import ValidateErrorException


class ParameterType(str, Enum):
    """参数支持的类型"""
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


class ParameterIn(str, Enum):
    """参数支持存放的位置"""
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    REQUEST_BODY = "request_body"


class OpenAPISchema(BaseModel):
    """OpenAPI规范 数据结构"""

    server: str = Field(default="", validate_default=True, description="工具提供者的服务基础地址")
    description: str = Field(default="", validate_default=True, description="工具提供者的描述信息")
    paths: dict[str, dict] = Field(default_factory=dict, validate_default=True, description="工具提供者的路径参数字典")

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """校验 server 字段"""
        if server is None or server == "":
            raise ValidateErrorException(message="server字段不能为空")

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        """校验 description 字段"""
        if description is None or description == "":
            raise ValidateErrorException(message="description字段不能为空")

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict[str, dict]) -> dict[str, str]:
        """校验 paths 信息：方法提取、oprationId 唯一标识，parameters 校验"""

        # path 不为空类型为字典
        if not paths or not isinstance(paths, dict):
            return ValidateErrorException("openapi_schema中的paths不能为空且必须为字典")

        # 提取 paths 中每个元素，并获取元素下 get/post对应的值
        methods = ["get", "post"]
        interfaces = []
        extra_paths = {}

        for path, path_item in paths.items():
            for method in methods:
                if method in path_item:
                    interfaces.append({
                        "path": path,
                        "method": method,
                        "operation": path_item[method]
                    })

        # 遍历提取到的所有接口并校验信息，涵盖operationId唯一标识，parameters参数
        operation_ids = []
        for interface in interfaces:

            # 校验 description&operationId&parameters
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidateErrorException("description 不能为空且为字符串")
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidateErrorException("operationId 不能为空且为字符串")
            if not isinstance(interface["operation"].get("parameters", []), list):
                raise ValidateErrorException("parameters 必须是列表或者为空")

            # 检测operationId是否是唯一的
            if interface["operation"]["operationId"] in operation_ids:
                raise ValidateErrorException(f"operationId 必须唯一，{interface["operation"]["operationId"]}出现重复")

            operation_ids.append(interface["operation"]["operationId"])

            # 校验 parameters 参数格式
            for parameter in interface["parameters"]:

                # 校验 name&in&description&required&type 参数
                if not isinstance(parameter.get("name"), str):
                    raise ValidateErrorException("parameter.name 参数必须为字符串且不为空")
                if not isinstance(parameter.get("description"), str):
                    raise ValidateErrorException("parameter.description 参数必须为字符串且不为空")
                if not isinstance(parameter.get("required"), str):
                    raise ValidateErrorException("parameter.required 参数必须为布尔值且不为空")

                if (
                        not isinstance(parameter.get("in"), str)
                        or parameter.get("in") not in ParameterIn.__members__.values()
                ):
                    raise ValidateErrorException(
                        f" parameter.in 参数必须为 {"/".join([item.value for item in ParameterIn])}"
                    )

                if (
                        not isinstance(parameter.get("type"), str)
                        or parameter.get("type") not in ParameterType.__members__.values()
                ):
                    raise ValidateErrorException(
                        f"parameter.type参数必须为{"/".join([item.value for item in ParameterType])}"
                    )

            # 组装数据并更新
            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [
                        {
                            "name": parameter.get("name"),
                            "in": parameter.get("in"),
                            "description": parameter.get("description"),
                            "required": parameter.get("required"),
                            "type": parameter.get("type"),
                        }
                        for parameter in interface["operation"].get("parameters", [])
                    ],
                }
            }

        return extra_paths
