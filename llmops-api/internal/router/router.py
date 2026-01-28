#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   router
@Time   :   2025/9/1 11:48
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import (
    AppHandler, BuiltinToolHandler, ApiToolHandler, UploadFileHandler,
    DatasetHandler, DocumentHandler, SegmentHandler, OAuthHandler, AuthHandler, AccountHandler)


@inject
@dataclass
class Router:
    """路由"""
    auth_handler: AuthHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler
    document_handler: DocumentHandler
    segment_handler: SegmentHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 将 URL 与对应的控制器方法绑定

        # 对话接口测试
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/apps/<uuid:app_id>/debug", methods=["POST"], view_func=self.app_handler.debug)

        # 授权认证
        bp.add_url_rule("/oauth/<string:provider_name>", view_func=self.oauth_handler.provider)
        bp.add_url_rule("/oauth/authorize/<string:provider_name>", methods=["POST"],
                        view_func=self.oauth_handler.authorize)
        bp.add_url_rule("/auth/password-login", methods=["POST"], view_func=self.auth_handler.password_login)
        bp.add_url_rule("/auth/logout", methods=["POST"], view_func=self.auth_handler.logout)

        # 账号管理 模块
        bp.add_url_rule("/account", view_func=self.account_handler.get_current_user)
        bp.add_url_rule("/account/password", methods=["POST"], view_func=self.account_handler.update_password)
        bp.add_url_rule("/account/name", methods=["POST"], view_func=self.account_handler.update_name)
        bp.add_url_rule("/account/avatar", methods=["POST"], view_func=self.account_handler.update_avatar)

        # 应用管理 模块
        bp.add_url_rule("/app", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/app/<uuid:id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)
        bp.add_url_rule("/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app)
        bp.add_url_rule("/app/<uuid:id>", view_func=self.app_handler.get_app)

        # 内置插件 模块
        bp.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule("/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
                        view_func=self.builtin_tool_handler.get_provider_tool)
        bp.add_url_rule("/builtin-tools/<string:provider_name>/icon",
                        view_func=self.builtin_tool_handler.get_provider_icon)
        bp.add_url_rule("/builtin-tools/categories",
                        view_func=self.builtin_tool_handler.get_categories)

        # 自定义插件 模块
        bp.add_url_rule("/api-tools/validate-openapi-schema", methods=["POST"],
                        view_func=self.api_tool_handler.validate_openapi_schema)
        bp.add_url_rule("/api-tools", methods=["POST"], view_func=self.api_tool_handler.create_api_tool_provider)
        bp.add_url_rule("/api-tools/<uuid:provider_id>/delete", methods=["POST"],
                        view_func=self.api_tool_handler.delete_api_tool_provider)
        bp.add_url_rule("/api-tools/<uuid:provider_id>", methods=["POST"],
                        view_func=self.api_tool_handler.update_api_tool_provider)
        bp.add_url_rule("/api-tools", view_func=self.api_tool_handler.get_api_tool_providers_with_page)
        bp.add_url_rule("/api-tools/<uuid:provider_id>", view_func=self.api_tool_handler.get_api_tool_provider)
        bp.add_url_rule("/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
                        view_func=self.api_tool_handler.get_api_tool)

        # 上传文件模块
        bp.add_url_rule("/upload-files/file", methods=["POST"], view_func=self.upload_file_handler.upload_file)
        bp.add_url_rule("/upload-files/image", methods=["POST"], view_func=self.upload_file_handler.upload_image)

        # 知识库模块
        bp.add_url_rule("/datasets", methods=["POST"], view_func=self.dataset_handler.create_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/delete", methods=["POST"],
                        view_func=self.dataset_handler.delete_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", methods=["POST"], view_func=self.dataset_handler.update_dataset)
        bp.add_url_rule("/datasets", view_func=self.dataset_handler.get_datasets_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", view_func=self.dataset_handler.get_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/queries", view_func=self.dataset_handler.get_dataset_queries)

        # 知识库模块-文档
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents", methods=["POST"],
                        view_func=self.document_handler.create_documents)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete", methods=["POST"],
                        view_func=self.document_handler.delete_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name", methods=["POST"],
                        view_func=self.document_handler.update_document_name)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled", methods=["POST"],
                        view_func=self.document_handler.update_document_enabled)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents",
                        view_func=self.document_handler.get_documents_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>",
                        view_func=self.document_handler.get_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/batch/<string:batch>",
                        view_func=self.document_handler.get_documents_status)

        # 知识库模块-文档-片段
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments", methods=["POST"],
                        view_func=self.segment_handler.create_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete",
                        methods=["POST"], view_func=self.segment_handler.delete_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                        methods=["POST"], view_func=self.segment_handler.update_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled",
                        methods=["POST"], view_func=self.segment_handler.update_segment_enabled)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                        view_func=self.segment_handler.get_segments_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                        view_func=self.segment_handler.get_segment)
        # 指定知识库进行召回测试
        bp.add_url_rule("/datasets/<uuid:dataset_id>/hit", methods=["POST"], view_func=self.dataset_handler.hit)

        # 在应用上注册蓝图
        app.register_blueprint(bp)
