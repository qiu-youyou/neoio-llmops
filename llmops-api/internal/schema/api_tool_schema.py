#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_schema
@Time   :   2025/12/8 11:13
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError, Optional

from internal.model import ApiToolProvider, ApiTool
from internal.schema import ListField
from pkg.paginator import PaginatorReq


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""
    openapi_schema = StringField("openapi_schema", validators=[DataRequired(
        message="openapi_schema 字符串不能为空"
    )])


class GetApiToolProvidersWithPageReq(PaginatorReq):
    """校验获取自定义工具提供者分页列表请求"""
    search_word = StringField("search_word", validators=[
        Optional()
    ])


class CreateApiToolReq(FlaskForm):
    """校验创建自定义工具请求"""
    name = StringField("name", validators=[
        DataRequired(message="工具供应商名称不能为空"),
        Length(min=1, max=30, message="工具供应商名称长度1-30")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="工具供应商图标不能为空"),
        URL(message="工具供应商的图标必须是URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema 字符串不能为空"),
    ])

    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers请求的数据是否正确，涵盖列表校验，列表元素校验"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers中的元素都应为字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers中的每个元素有且只有key&value两个属性")


class UpdateApiToolProviderReq(CreateApiToolReq):
    """校验更新自定义工具请求"""
    pass


class GetApiToolProvidersWithPageResp(Schema):
    """获取自定义工具提供者分页列表数据响应"""
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolProviderResp(Schema):
    """获取自定义提供者响应信息"""
    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    """获取自定义工具参数详情响应"""
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, default=[])
    provider = fields.Dict()

    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k: v for k, v in parameter.items() if k != "in"} for parameter in data.parameters],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            }
        }
