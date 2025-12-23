#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   indexing_service
@Time   :   2025/12/22 22:22
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class IndexingService(BaseService):
    """索引构建服务"""
    db: SQLAlchemy

    def build_documents(self, document_ids: list[UUID]) -> None:
        """根据文档id列表 构建知识库文档 涵盖加载、分割、索引构建、存储等"""

        # todo:::
