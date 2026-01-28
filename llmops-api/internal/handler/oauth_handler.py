#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   oauth_handler
@Time   :   2026/1/27 21:37
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from injector import inject

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    """第三方授权认证"""

    oauth_service: OAuthService

    def provider(self, provider_name: str):
        """根据第三方名称获取授权地址"""
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)
        redirect_uri = oauth.get_authorization_url()
        return success_json({"redirect_uri": redirect_uri})

    def authorize(self, provider_name: str):
        """根据第三方名称+Code 获取授权凭证信息"""
        req = AuthorizeReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        resp = AuthorizeResp()
        return success_json(resp.dump(credential))
