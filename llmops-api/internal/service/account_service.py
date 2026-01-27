#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   account_service
@Time   :   2026/1/26 21:43
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import Account, AccountOAuth
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jwt_service import JWTService


@inject
@dataclass
class AccountService(BaseService):
    """账户服务"""
    db: SQLAlchemy
    jwt_service: JWTService

    def get_account(self, account_id: UUID) -> Account:
        """获取指定账号信息"""
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(self, provider_name: str, openid: str) -> AccountOAuth:
        """根据第三方名称+OPENID获取授权记录"""
        account_oauth = self.db.session.query(AccountOAuth).filter(
            AccountOAuth.provider == provider_name,
            AccountOAuth.openid == openid,
        ).one_or_none()
        return account_oauth

    def get_account_by_email(self, email: str) -> Account:
        """根据邮箱获取账号信息"""
        account = self.db.session.query(Account).filter(Account.email == email).one_or_none()
        return account
