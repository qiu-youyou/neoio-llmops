#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_key_service
@Time   :   2026/2/25 14:42
@Author :   s.qiu@foxmail.com
"""
import secrets
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from pkg.paginator import Paginator, PaginatorReq
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..exception import ForbiddenException
from ..model import ApiKey, Account
from ..schema.api_key_schema import CreateApiKeyReq


@inject
@dataclass
class ApiKeyService(BaseService):
    """开放 API 密钥服务"""
    db: SQLAlchemy

    def get_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """根据密钥 ID 获取密钥"""
        api_key = self.get(ApiKey, api_key_id)
        if not api_key or api_key.account_id != account.id:
            raise ForbiddenException("密钥不存在或无权限")
        return api_key

    def create_api_key(self, req: CreateApiKeyReq, account: Account) -> ApiKey:
        """新增 API 密钥"""
        api_key = self.create(
            ApiKey,
            account_id=account.id,
            api_key=self.generate_api_key(),
            is_active=req.is_active.data,
            remark=req.remark.data,
        )
        return api_key

    def delete_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """删除 API 密钥"""
        api_key = self.get_api_key(api_key_id, account)
        self.delete(api_key)
        return api_key

    def update_api_key(self, api_key_id: UUID, account: Account, **kwargs) -> ApiKey:
        """修改 API 密钥信息"""
        api_key = self.get_api_key(api_key_id, account)
        self.update(api_key, **kwargs)
        return api_key

    def update_api_key_is_active(self, api_key_id: UUID, account: Account, **kwargs):
        """修改 API 密钥状态"""
        api_key = self.get_api_key(api_key_id, account)
        self.update(api_key, **kwargs)
        return api_key

    def get_api_keys_with_page(self, req: PaginatorReq, account: Account) -> tuple[list[ApiKey], Paginator]:
        """获取 API 密钥分页列表"""
        paginator = Paginator(db=self.db, req=req)
        filters = [ApiKey.account_id == account.id]
        api_keys = paginator.paginate(self.db.session.query(ApiKey).filter(*filters).order_by(desc("created_at")))
        return api_keys, paginator

    def get_api_by_by_credential(self, api_key: str) -> ApiKey:
        """根据传递的凭证信息获取ApiKey记录"""
        return self.db.session.query(ApiKey).filter(ApiKey.api_key == api_key).one_or_none()

    @classmethod
    def generate_api_key(cls, api_key_prefix: str = "llmops-v1/") -> str:
        """生成长度为48的API密钥 携带前缀"""
        return api_key_prefix + secrets.token_urlsafe(48)
