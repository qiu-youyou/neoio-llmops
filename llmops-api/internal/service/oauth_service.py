#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   oauth_service
@Time   :   2026/1/27 21:02
@Author :   s.qiu@foxmail.com
"""
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from flask import request
from injector import inject

from internal.exception import NotFoundException
from pkg.oauth import OAuth, GithubOAuth
from pkg.sqlalchemy import SQLAlchemy
from . import AccountService
from .base_service import BaseService
from .jwt_service import JWTService
from ..model import AccountOAuth


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

        # 获取授权记录
        account_oauth = self.account_service.get_account_oauth_by_provider_name_and_openid(
            provider_name,
            oauth_user_info.id,
        )

        # 如果是第一次授权 检查是否存在该账号 不存在则注册
        if not account_oauth:
            account = self.account_service.get_account_by_email(oauth_user_info.email)
            if not account:
                account = self.account_service.create_account(name=oauth_user_info.name, email=oauth_user_info.email)
            # 添加授权认证的记录
            account_oauth = self.create(AccountOAuth, account_id=account.id,
                                        provider=provider_name,
                                        openid=oauth_user_info.id,
                                        encrypted_token=oauth_access_token)
        # 有记录 查找账号信息
        else:
            account = self.account_service.get_account(account_oauth.account_id)

        # 更新账号 最后登陆时间以及IP
        self.update(account, last_login_at=datetime.now(), last_login_ip=request.remote_addr)
        self.update(account_oauth, encrypted_token=oauth_access_token)

        # 生成授权凭证
        expire_at = int((datetime.now() + timedelta(days=1)).timestamp())
        payload = {"sub": str(account.id), "iss": "llmops", "exp": expire_at}

        access_token = self.jwt_service.generate_token(payload)
        return {"expire_at": expire_at, "access_token": access_token}
