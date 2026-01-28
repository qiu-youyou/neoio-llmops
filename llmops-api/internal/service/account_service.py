#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   account_service
@Time   :   2026/1/26 21:43
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject

from internal.model import Account, AccountOAuth
from pkg.password import compare_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jwt_service import JWTService
from ..exception import FailException


@inject
@dataclass
class AccountService(BaseService):
    """账户服务"""
    db: SQLAlchemy
    jwt_service: JWTService

    def get_account(self, account_id: UUID) -> Account:
        """获取指定账号信息"""
        return self.get(Account, account_id)

    def get_account_by_email(self, email: str) -> Account:
        """根据邮箱获取账号信息"""
        account = self.db.session.query(Account).filter(Account.email == email).one_or_none()
        return account

    def get_account_oauth_by_provider_name_and_openid(self, provider_name: str, openid: str) -> AccountOAuth:
        """根据第三方名称+OPENID获取授权记录"""
        account_oauth = self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid,
        ).one_or_none()
        return account_oauth

    def create_account(self, **kwargs) -> Account:
        """创建账号信息"""
        account = self.create(Account, **kwargs)
        return account

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """账号+密码 登录"""

        # 账号是否存在
        account = self.get_account_by_email(email)
        if account is None:
            raise FailException("账号不存在或密码错误，请重试")

        if not account.is_password_set or not compare_password(password, account.password, account.password_salt):
            raise FailException("账号不存在或密码错误，请重试")

        # 生成凭证信息
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)
