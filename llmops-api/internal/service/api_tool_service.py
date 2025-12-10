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
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq, GetApiToolProvidersWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiToolService(BaseService):
    db: SQLAlchemy
    """自定义插件服务"""

    def get_api_tool_providers_with_page(self, req: GetApiToolProvidersWithPageReq) -> tuple[list[Any], Paginator]:
        """获取自定义插件服务提供者分页列表数据"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 筛选器&分页查询器
        filters = [ApiToolProvider.account_id == account_id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word}%"))
        paginator = Paginator(self.db, req)

        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    def create_api_tool_provider(self, req: CreateApiToolReq) -> None:
        """创建自定义插件"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 校验 openapi_schema
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 该账号下是否有同名的工具提供者
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account_id,
            name=req.name.data,
        ).one_or_none()

        if api_tool_provider:
            raise ValidateErrorException(f"该工具提供者名字{req.name.data}已存在")

        # 创建工具提供者
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )

        # 创建自定义工具
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def update_api_tool_provider(self, req: CreateApiToolReq, provider_id: UUID) -> None:
        """更新自定义插件"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 校验 openapi_schema
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 是否存在该供应商
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        # 更新的数据是否存在
        check_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.account_id == account_id,
            ApiToolProvider.name == req.name.data,
            ApiToolProvider.id != api_tool_provider.id
        ).one_or_none()
        if check_api_tool_provider:
            raise ValidateErrorException(f"该工具提供者名字{req.name.data}已存在")

        # 先删除该提供商下的所有工具
        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id,
            ).delete()

        # 更新该提供商以及工具
        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
        )

        # 创建自定义工具
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def delete_api_tool_provider(self, provider_id: UUID):
        """根据 provider_id 删除对应提供商"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供商不存在")

        # 删除该工具提供商下的所有工具
        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(provider_id == provider_id, account_id == account_id).delete()
            self.db.session.delete(api_tool_provider)

    def get_api_tool_provider(self, provider_id: UUID) -> ApiToolProvider:
        """根据传递的provider_id获取工具提供者的原始信息"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该插件提供者不存在")
        return api_tool_provider

    def get_api_tool(self, provider_id: UUID, tool_name) -> ApiTool:
        """provider_id+tool_name获取对应工具的参数详情信息"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 工具是否存在
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name,
        ).one_or_none()

        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException("该工具不存在")

        # 查询该工具的提供者
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        api_tool.provider = api_tool_provider
        return api_tool

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> Any:
        """解析传递的 openapi_schema"""
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateErrorException("传递的数据必须符合OpenAPI规范的JSON字符串")

        return OpenAPISchema(**data)
