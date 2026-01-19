#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   full_text_retriever
@Time   :   2026/1/19 10:35
@Author :   s.qiu@foxmail.com
"""
from typing import List, Counter
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from internal.model import KeywordTable, Segment
from internal.service import JiebaService
from pkg.sqlalchemy import SQLAlchemy


class FullTextRetriever(BaseRetriever):
    """全文检索"""
    db: SQLAlchemy
    dataset_ids: List[UUID]
    jieba_services: JiebaService
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        """query 执行关键词检索"""

        # query 执行关键词检索获取 langchain 文档
        keywords = self.jieba_services.extract_keywords(query, 10)

        # 查找知识库关键词表
        keyword_tables = [
            keyword_table for keyword_table, in
            self.db.session.query(KeywordTable).with_entities(KeywordTable.keyword_table).filter(
                KeywordTable.dataset_id.in_(self.dataset_ids)
            ).all()
        ]

        all_ids = []
        for keyword_table in keyword_tables:
            for keyword, segment_id in keyword_table.items():
                if keyword in keywords:
                    all_ids.extend(segment_id)

        id_counter = Counter(all_ids)

        # 获取频率最高的 K 条数据
        k = self.search_kwargs.get("k", 4)
        top_k_ids = id_counter.most_common(k)

        # 检索数据库获取片段列表
        segments = self.db.session.query(Segment).filter(Segment.id.in_([id for id, _ in top_k_ids])).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 根据频率进行排序
        sorted_segments = [segment_dict[str(id)] for id, freq in top_k_ids if id in segment_dict]

        # 构建 langchain 文档
        lc_documents = [LCDocument(
            page_content=segment.content,
            metadata={
                "account_id": str(segment.account_id),
                "dataset_id": str(segment.dataset_id),
                "document_id": str(segment.document_id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": True,
                "segment_enabled": True,
                "score": 0,
            }
        ) for segment in sorted_segments]

        return lc_documents
