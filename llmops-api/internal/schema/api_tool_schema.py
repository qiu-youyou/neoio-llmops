#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_schema
@Time   :   2025/12/8 11:13
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError

from internal.schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""
    openapi_schema = StringField("openapi_schema", validators=[DataRequired(
        message="openapi_schema 字符串不能为空"
    )])


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
