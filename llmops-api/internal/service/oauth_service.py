#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   oauth_service
@Time   :   2026/1/27 21:02
@Author :   s.qiu@foxmail.com
"""
import os
from dataclasses import dataclass
from typing import Any

from injector import inject

from internal.exception import NotFoundException
from pkg.oauth import OAuth, GithubOAuth
from pkg.sqlalchemy import SQLAlchemy
from . import AccountService
from .base_service import BaseService
from .jwt_service import JWTService


@inject
@dataclass
class OAuthService(BaseService):
    """第三方授权认证服务"""

    db: SQLAlchemy
    jwt_service: JWTService
    account_service: AccountService

    @classmethod
    def get_all_oauth(cls) -> dict[str, OAuth]:
        """获取项目支持的第三方授权认证方式"""
        # 1.实例化集成的第三方授权认证OAuth
        github = GithubOAuth(
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            redirect_uri=os.getenv("GITHUB_REDIRECT_URI"),
        )

        return {"github": github}

    @classmethod
    def get_oauth_by_provider_name(cls, provider_name: str) -> OAuth:
        """根据传递的服务提供商名字获取授权服务"""
        all_oauth = cls.get_all_oauth()
        oauth = all_oauth.get(provider_name)

        if oauth is None:
            raise NotFoundException(f"该授权方式[{provider_name}]不存在")

        return oauth

    def oauth_login(self, provider_name: str, code: str) -> dict[str, Any]:
        """第三方授权登录 反回凭证信息"""
        oauth = self.get_oauth_by_provider_name(provider_name)
        oauth_access_token = oauth.get_access_token(code)
        oauth_user_info = oauth.get_user_info(oauth_access_token)  # id/name/email

        # 获取以前的授权记录
        account_oauth = self.account_service.get_account_oauth_by_provider_name_and_openid(
            provider_name,
            oauth_user_info.id,
        )
        