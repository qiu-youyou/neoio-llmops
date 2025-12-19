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

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler, UploadFileHandler
from internal.handler.dataset_handler import DatasetHandler


@inject
@dataclass
class Router:
    """路由"""
    app_handle: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 将 URL 与对应的控制器方法绑定
        bp.add_url_rule("/test", methods=["POST"], view_func=self.app_handle.test)
        # 对话接口测试
        bp.add_url_rule("/apps/<uuid:app_id>/debug", methods=["POST"], view_func=self.app_handle.debug)

        # 应用管理 模块
        bp.add_url_rule("/app/<uuid:id>", view_func=self.app_handle.get_app)
        bp.add_url_rule("/app", methods=["POST"], view_func=self.app_handle.create_app)
        bp.add_url_rule("/app/<uuid:id>", methods=["POST"], view_func=self.app_handle.update_app)
        bp.add_url_rule("/app/<uuid:id>/delete", methods=["POST"], view_func=self.app_handle.delete_app)

        # 内置插件 模块
        bp.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule("/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
                        view_func=self.builtin_tool_handler.get_provider_tool)
        bp.add_url_rule("/builtin-tools/<string:provider_name>/icon",
                        view_func=self.builtin_tool_handler.get_provider_icon, )
        bp.add_url_rule("/builtin-tools/categories",
                        view_func=self.builtin_tool_handler.get_categories, )

        # 自定义插件 模块
        bp.add_url_rule("/api-tools/validate-openapi-schema", methods=["POST"],
                        view_func=self.api_tool_handler.validate_openapi_schema)
        bp.add_url_rule("/api-tools", view_func=self.api_tool_handler.get_api_tool_providers_with_page)
        bp.add_url_rule("/api-tools", methods=["POST"],
                        view_func=self.api_tool_handler.create_api_tool_provider)
        bp.add_url_rule("/api-tools/<uuid:provider_id>", methods=["POST"],
                        view_func=self.api_tool_handler.update_api_tool_provider)
        bp.add_url_rule("/api-tools/<uuid:provider_id>/delete", methods=["POST"],
                        view_func=self.api_tool_handler.delete_api_tool_provider)
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
            view_func=self.api_tool_handler.get_api_tool,
        )

        # 上传文件模块
        bp.add_url_rule(
            "/upload-files/file",
            methods=["POST"],
            view_func=self.upload_file_handler.upload_file,
        )
        bp.add_url_rule(
            "/upload-files/image",
            methods=["POST"],
            view_func=self.upload_file_handler.upload_image,
        )

        # 知识库模块
        bp.add_url_rule(
            "/datasets", view_func=self.dataset_handler.get_datasets_with_page
        )
        bp.add_url_rule(
            "/datasets", methods=["POST"], view_func=self.dataset_handler.create_dataset
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>", view_func=self.dataset_handler.get_dataset
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>",
            methods=["POST"],
            view_func=self.dataset_handler.update_dataset,
        )
        bp.add_url_rule("/datasets/embeddings", view_func=self.dataset_handler.embeddings_query)

        # 在应用上注册蓝图
        app.register_blueprint(bp)
