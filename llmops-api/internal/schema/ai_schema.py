#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   ai_schema
@Time   :   2026/2/25 09:09
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, UUID


class OptimizePromptReq(FlaskForm):
    """优化Prompt请求结构"""
    prompt = StringField("prompt", validators=[
        DataRequired("prompt 不能为空"),
        Length(max=2000, message="prompt长度最大为2000个字符")
    ])


class GenerateSuggestedQuestionsReq(FlaskForm):
    """问题建议列表请求结构"""
    message_id = StringField("message_id", validators=[
        DataRequired("message_id 不能为空"),
        UUID("message_id 格式必须为 uuid")
    ])
