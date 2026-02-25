#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   middleware
@Time   :   2026/1/26 21:25
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from typing import Optional

from flask import Request
from injector import inject

from internal.exception import UnauthorizedException
from internal.model import Account
from internal.service import JWTService, AccountService, ApiKeyService


@inject
@dataclass
class Middleware:
    """应用中间件"""
    jwt_service: JWTService
    account_service: AccountService
    api_key_service: ApiKeyService

    def request_loader(self, request: Request) -> Optional[Account]:
        """登录管理器的 请求加载器"""

        if request.blueprint == "llmops":
            # 校验 access_token
            access_token = self._validate_credential(request)
            # 解析 token 获取用户信息
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            account = self.account_service.get_account(account_id)
            return account
        elif request.blueprint == "openapi":
            # 校验 api_key
            api_key = self._validate_credential(request)
            api_key_record = self.api_key_service.get_api_by_by_credential(api_key)
            if not api_key_record or not api_key_record.is_active:
                raise UnauthorizedException("API密钥不存在或未启用")
            return api_key_record.account
        else:
            return None

    @classmethod
    def _validate_credential(self, request: Request) -> str:
        """校验请求中的凭证信息 access_token / api_key"""
        auth_header = request.headers.get("Authorization")
        # 请求头中没有 Authorization
        if not auth_header:
            raise UnauthorizedException("缺少TOKEN，请登录后重试")
        # 没有空格分隔符 Authorization: Bearer access_token
        if " " not in auth_header:
            raise UnauthorizedException("TOKEN格式错误，请登录后重试")

        # 按空格分隔 必须符合 Bearer access_token
        auth_schema, credential = auth_header.split(None, 1)
        if auth_schema.lower() != "bearer":
            raise UnauthorizedException("无权限访问，请登录后重试")

        return credential
