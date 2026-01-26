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

from internal.model import Account
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
        """获取指定账号模型"""
        return self.get(Account, account_id)
