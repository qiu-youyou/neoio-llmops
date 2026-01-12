#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   keyword_table_service
@Time   :   2025/12/25 09:58
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from injector import inject
from redis import Redis

from internal.entity.cache_entity import LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE, LOCK_EXPIRE_TIME
from internal.model import KeywordTable, Segment
from internal.service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class KeywordTableService(BaseService):
    """关键词服务"""
    db: SQLAlchemy
    redis_client: Redis

    def get_keyword_table_from_dataset_id(self, dataset_id) -> KeywordTable:
        """获取知识库的 关键词表"""
        keyword_table = self.db.session.query(KeywordTable).filter(KeywordTable.dataset_id == dataset_id).one_or_none()
        if keyword_table is None:
            keyword_table = self.create(KeywordTable, dataset_id=dataset_id, keyword_table={})

        return keyword_table

    def delete_keyword_table_from_ids(self, dataset_id, segment_ids: list[UUID]) -> None:
        """删除指定知识库下关键词表多余的数据"""
        # 上锁避免并发时拿到错误数据
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = keyword_table_record.keyword_table.copy()

            segment_ids_to_delete = set([str(segment_id) for segment_id in segment_ids])
            keywords_to_delete = set()

            # 遍历关键词判断更新
            for keyword, ids in keyword_table.items():
                ids_set = set(ids)
                if segment_ids_to_delete.intersection(ids_set):
                    keyword_table[keyword] = list(ids_set.difference(segment_ids_to_delete))
                    if not keyword_table[keyword]:
                        keywords_to_delete.add(keyword)

            # 检测空关键词数据并删除（关键词并没有映射任何字段id的数据）
            for keyword in keywords_to_delete:
                del keyword_table[keyword]

            self.update(keyword_table_record, keyword_table=keyword_table)

    def add_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[UUID]) -> None:
        """在指定知识库的关键词表中添加关键词"""
        # 知识库新增关键词 上锁避免并发时拿到错误数据
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 获取指定关键词表
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = {"field": set(value) for field, value in keyword_table_record.keyword_table.items()}

            # 查找片段的关键词信息
            segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.keywords).filter(
                Segment.id.in_(segment_ids)).all()

            # 将新的关键词添加到关键词表中
            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            # 更新关键词表
            self.update(keyword_table_record,
                        keyword_table={field: list(value) for field, value in keyword_table.items()})
