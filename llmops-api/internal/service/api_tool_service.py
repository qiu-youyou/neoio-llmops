# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_service
@Time   :   2025/12/8 11:25
@Author :   s.qiu@foxmail.com
"""

import json
from dataclasses import dataclass
from typing import Any

from injector import inject

from internal.exception import ValidateErrorException


@inject
@dataclass
class ApiToolService:
    """自定义 API 插件服务"""

    @classmethod
    def parse_openapi_schema(self, openapi_schema_str: str) -> Any:
        """解析传递的 openapi_schema"""
        try:
            data = json.loads(openapi_schema_str)
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateErrorException("传递的数据必须符合OpenAPI规范的JSON字符串")
