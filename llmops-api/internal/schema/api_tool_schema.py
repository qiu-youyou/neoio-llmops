#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool_schema
@Time   :   2025/12/8 11:13
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchemaReq(FlaskForm):
    openapi_schema = StringField("openapi_schema", validators=[DataRequired(
        message="openapi_schema 字符串不能为空"
    )])
