#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_handle
@Time   :   2025/12/8 10:55
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from flask import request
from flask_login import login_required, current_user
from injector import inject
from sqlalchemy import UUID

from internal.schema.api_tool_schema import (
    ValidateOpenAPISchemaReq, CreateApiToolReq, GetApiToolProvidersWithPageReq, UpdateApiToolProviderReq,
    GetApiToolProvidersWithPageResp, GetApiToolProviderResp, GetApiToolResp)
from internal.service import ApiToolService
from pkg.paginator import PageModel
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class ApiToolHandler:
    api_tool_service: ApiToolService
    """自定义插件 处理器"""

    @login_required
    def get_api_tool_providers_with_page(self):
        """获取自定义插件 提供者列表信息，该接口支持分页"""
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_providers, paginator = self.api_tool_service.get_api_tool_providers_with_page(req, current_user)

        resp = GetApiToolProvidersWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(api_tool_providers), paginator=paginator))

    @login_required
    def create_api_tool_provider(self):
        """创建自定义插件"""
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.create_api_tool_provider(req, current_user)
        return success_message("创建自定义插件成功")

    @login_required
    def update_api_tool_provider(self, provider_id: UUID):
        """更新自定义信息"""
        req = UpdateApiToolProviderReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_tool_service.update_api_tool_provider(req, provider_id, current_user)
        return success_message("更新自定义插件成功")

    @login_required
    def get_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id获取工具提供者的原始信息"""
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id, current_user)
        resp = GetApiToolProviderResp()
        return success_json(resp.dump(api_tool_provider))

    @login_required
    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id+tool_name获取工具的详情信息"""
        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name, current_user)
        resp = GetApiToolResp()
        return success_json(resp.dump(api_tool))

    @login_required
    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除对应的工具提供者信息"""
        self.api_tool_service.delete_api_tool_provider(provider_id, current_user)
        return success_message(f"删除自定义插件成功", )

    @login_required
    def validate_openapi_schema(self):
        """校验 openapi_schema 字符串格式"""
        req = ValidateOpenAPISchemaReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 解析传递的数据
        self.api_tool_service.parse_openapi_schema(req.openapi_schema.data)
        return success_message("数据校验成功")
