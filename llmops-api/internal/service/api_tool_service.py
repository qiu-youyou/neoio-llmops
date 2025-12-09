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

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schema import CreateApiToolReq
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiToolService(BaseService):
    db: SQLAlchemy
    """自定义 API 插件服务"""

    def create_api_tool(self, req: CreateApiToolReq) -> None:
        """创建自定义 api 工具"""

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
        print(api_tool_provider)

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

    def delete_api_tool_provider(self, provider_id: UUID) -> Any:
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
