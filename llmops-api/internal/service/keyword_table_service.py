#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   keyword_table_service
@Time   :   2025/12/25 09:58
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from injector import inject

from internal.model import KeywordTable
from internal.service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class KeywordTableService(BaseService):
    """关键词服务"""
    db: SQLAlchemy

    def get_keyword_table_from_dataset_id(self, dataset_id) -> KeywordTable:
        """获取知识库的 关键词表"""
        keyword_table = self.db.session.query(KeywordTable).filter(KeywordTable.id == dataset_id).one_or_none()
        if keyword_table is None:
            keyword_table = self.create(KeywordTable, dataset_id=dataset_id, keyword_table={})

        return keyword_table
