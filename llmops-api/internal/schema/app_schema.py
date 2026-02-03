#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_schema
@Time   :   2025/9/5 14:19
@Author :   s.qiu@foxmail.com
"""

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

from internal.lib.helper import datetime_to_timestamp
from internal.model import App, AppConfigVersion
from pkg.paginator import PaginatorReq


class CreateAppReq(FlaskForm):
    """创建应用请求结构"""
    name = StringField("name", validators=[
        DataRequired("应用名称不能为空"), Length(max=30, message="应用名称最长为30个字符")])
    icon = StringField("icon", validators=[
        DataRequired("应用图标不能为空"), URL(message="图标格式必须是URL链接")
    ])
    description = StringField("description", validators=[
        Length(max=800, message="应用描述最长为800个字符")
    ])


class UpdateAppReq(FlaskForm):
    """修改应用请求结构"""
    name = StringField("name", validators=[
        DataRequired("应用名称不能为空"), Length(max=30, message="应用名称最长为30个字符")])
    icon = StringField("icon", validators=[
        DataRequired("应用图标不能为空"), URL(message="图标格式必须是URL链接")
    ])
    description = StringField("description", validators=[
        Length(max=800, message="应用描述最长为800个字符")
    ])


class GetAppResp(Schema):
    """获取应用基础信息响应结构"""
    id = fields.UUID(dump_default="")
    debug_conversation_id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    status = fields.String(dump_default="")
    draft_updated_at = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: App, **kwargs):
        return {
            "id": data.id,
            "debug_conversation_id": data.debug_conversation_id if data.debug_conversation_id else "",
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "draft_updated_at": datetime_to_timestamp(data.draft_app_config.updated_at),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetPublishHistoriesWithPageReq(PaginatorReq):
    """获取发布历史配置信息分页"""


class GetPublishHistoriesWithPageResp(Schema):
    id = fields.UUID(dump_default="")
    version = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: AppConfigVersion, **kwargs):
        return {
            "id": data.id,
            "version": data.version,
            "created_at": datetime_to_timestamp(data.created_at),
        }


class FallbackHistoryToDraftReq(FlaskForm):
    """回退历史版本到当前草稿请求"""
    app_config_version_id = StringField("app_config_version_id", validators=[
        DataRequired("回退版本id不能为空")
    ])


class UpdateDebugConversationSummaryReq(FlaskForm):
    """更新应用会话长期记忆请求体"""
    summary = StringField("summary", default="")


class DebugChatReq(FlaskForm):
    """应用调试会话请求结构体"""
    query = StringField("query", validators=[
        DataRequired("用户提问不能为空"),
    ])


class CompletionReq(FlaskForm):
    """基础聊天接口请求验证"""
    # 必填、长度最大为2000
    query = StringField("query", validators=[
        DataRequired(message="用户的提问是必填"),
        Length(max=2000, message="用户的提问最大长度是2000"),
    ])
