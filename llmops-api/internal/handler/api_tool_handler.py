#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_handle
@Time   :   2025/12/8 10:55
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from injector import inject
from sqlalchemy import UUID

from internal.schema.api_tool_schema import ValidateOpenAPISchemaReq
from internal.service import ApiToolService
from pkg.response import validate_error_json, success_message


@inject
@dataclass
class ApiToolHandler:
    api_tool_service: ApiToolService
    """自定义 API 插件 处理器"""

    def get_api_tool_providers_with_page(self):
        """获取API工具提供者列表信息，该接口支持分页"""

    def create_api_tool_provider(self):
        """创建自定义API工具"""

    def update_api_tool_provider(self, provider_id: UUID):
        """更新自定义API工具提供者信息"""

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id+tool_name获取工具的详情信息"""

    def get_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id获取工具提供者的原始信息"""

    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除对应的工具提供者信息"""

    def validate_openapi_schema(self):
        """校验 openapi_schema 字符串格式"""
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 解析传递的数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)

        return success_message("数据校验成功")
