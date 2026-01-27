#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   oauth_schema
@Time   :   2026/1/27 21:40
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms import StringField
from wtforms.validators import DataRequired


class AuthorizeReq(FlaskForm):
    """第三方授权认证请求体"""
    code = StringField("code", validators=[DataRequired("CODE不能为空")])


class AuthorizeResp(Schema):
    """第三方授权认证响应结构"""
    access_token = fields.String()
    expire_at = fields.Integer()
