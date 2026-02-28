#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_app_handler
@Time   :   2026/2/28 21:37
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.builtin_app_schema import GetBuiltinAppCategoriesResp, GetBuiltinAppsResp, AddBuiltinAppToSpaceReq
from internal.service import BuiltinAppService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class BuiltinAppHandler:
    """内置应用处理器"""
    builtin_app_service: BuiltinAppService

    @login_required
    def get_builtin_app_categories(self):
        """获取内置应用分类列表"""
        categories = self.builtin_app_service.get_categories()
        resp = GetBuiltinAppCategoriesResp(many=True)
        return success_json(resp.dump(categories))

    @login_required
    def get_builtin_apps(self):
        """获取内置应用模版列表"""
        builtin_apps = self.builtin_app_service.get_builtin_apps()
        resp = GetBuiltinAppsResp(many=True)
        return success_json(resp.dump(builtin_apps))

    @login_required
    def add_builtin_app_to_space(self):
        """内置应用模板添加到工作区"""
        req = AddBuiltinAppToSpaceReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app = self.builtin_app_service.add_builtin_app_to_space(req.builtin_app_id.data, current_user)
        return success_json({"id": app.id})
