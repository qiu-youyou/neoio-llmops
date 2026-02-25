#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_key_handler
@Time   :   2026/2/25 14:38
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import current_user, login_required
from injector import inject

from internal.schema.api_key_schema import CreateApiKeyReq, UpdateApiKeyReq, UpdateApiKeyIsActiveReq, \
    GetApiKeysWithPageResp
from internal.service import ApiKeyService
from pkg.paginator import PaginatorReq, PageModel
from pkg.response import validate_error_json, success_message, success_json


@inject
@dataclass
class ApiKeyHandler:
    """开放 API 密钥处理器"""
    api_key_service: ApiKeyService

    @login_required
    def create_api_key(self):
        """新增 API 密钥"""
        req = CreateApiKeyReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_key_service.create_api_key(req, current_user)
        return success_message("创建API密钥成功")

    @login_required
    def delete_api_key(self, api_key_id: UUID):
        """删除 API 密钥"""
        self.api_key_service.delete_api_key(api_key_id, current_user)
        return success_message("删除API密钥成功")

    @login_required
    def update_api_key(self, api_key_id: UUID):
        """修改 API 密钥信息"""
        req = UpdateApiKeyReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_key_service.update_api_key(api_key_id, current_user, **req.data)
        return success_message("修改API密钥成功")

    @login_required
    def update_api_key_is_active(self, api_key_id: UUID):
        """修改 API 密钥状态"""
        req = UpdateApiKeyIsActiveReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.api_key_service.update_api_key_is_active(api_key_id, current_user, **req.data)
        return success_message("修改API密钥状态成功")

    @login_required
    def get_api_keys_with_page(self):
        """获取 API 密钥分页列表"""
        req = PaginatorReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        api_keys, paginator = self.api_key_service.get_api_keys_with_page(req, current_user)
        resp = GetApiKeysWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(api_keys), paginator=paginator))
