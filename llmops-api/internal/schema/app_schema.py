#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_schema
@Time   :   2025/9/5 14:19
@Author :   s.qiu@foxmail.com
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class TestReq(FlaskForm):
    query = StringField("query", validators=[
        DataRequired(message="query字段为必填"),
        Length(max=20, message="query字段最大长度为10")
    ])


class CompletionReq(FlaskForm):
    """基础聊天接口请求验证"""
    # 必填、长度最大为2000
    query = StringField("query", validators=[
        DataRequired(message="用户的提问是必填"),
        Length(max=2000, message="用户的提问最大长度是2000"),
    ])
