#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   account_service
@Time   :   2026/1/26 21:43
@Author :   s.qiu@foxmail.com
"""
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from flask import request
from injector import inject

from internal.exception import FailException
from internal.model import Account, AccountOAuth
from pkg.password import compare_password, hash_password
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

    def get_account_by_email(self, email: str):
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

    def update_account(self, account: Account, **kwargs) -> Account:
        """更新当前账户信息"""
        account = self.update(account, **kwargs)
        return account

    def update_password(self, account: Account, password: str, ) -> Account:
        """更新当前账号密码信息"""
        # 生成密码随机盐值
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # 利用盐值和password进行加密
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        # 更新账号信息
        self.update_account(account, password=base64_password_hashed, password_salt=base64_salt)

        return account

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """账号+密码 登录"""

        # 账号是否存在
        account = self.get_account_by_email(email)
        if not account:
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

        # 更新账号登录信息
        self.update(account, last_login_at=datetime.now(), last_login_ip=request.remote_addr)

        return {"expire_at": expire_at, "access_token": access_token}
