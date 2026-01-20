#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   retrieval_service
@Time   :   2026/1/16 16:55
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document as LCDocument
from sqlalchemy import update

from internal.entity.dataset_entity import RetrievalStrategy, RetrievalSource
from internal.exception import NotFoundException
from internal.model import Dataset, DatasetQuery, Segment
from internal.service.base_service import BaseService
from internal.service.jieba_service import JiebaService
from internal.service.vector_database_service import VectorDatabaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class RetrievalService(BaseService):
    """检索服务"""
    db: SQLAlchemy
    jieba_service: JiebaService
    vector_database_service: VectorDatabaseService

    def search_in_datasets(
            self,
            dataset_ids: list[UUID],
            query: str,
            k: int = 4,
            score: float = 0,
            retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
            retrival_source: str = RetrievalSource.HIT_TESTING,
    ) -> list[LCDocument]:
        """知识库检索 返回检索文档+得分 全文检索则得分为0"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 提取知识库列表校验权限
        datasets = self.db.session.query(Dataset).filter(Dataset.id.in_(dataset_ids),
                                                         Dataset.account_id == account_id).all()
        if datasets is None or len(datasets) == 0:
            raise NotFoundException("当前无知识库可进行检索")
        dataset_ids = [datasets.id for datasets in datasets]

        # 构建不同种类检索器
        from internal.core.retrievers import SemanticRetriever, FullTextRetriever
        # 相似性/向量 检索器
        semantic_retriever = SemanticRetriever(
            dataset_ids=dataset_ids,
            vector_store=self.vector_database_service.vector_store,
            search_kwargs={"k": k, "score_threshold": score},
        )
        # 全文检索器
        full_text_retriever = FullTextRetriever(
            db=self.db,
            dataset_ids=dataset_ids,
            jieba_services=self.jieba_service,
            search_kwargs={"k": k},
        )
        # 混合检索器
        hybrid_retriever = EnsembleRetriever(retrievers=[semantic_retriever, full_text_retriever], weights=[0.5, 0.5])

        # 执行不同检索策略
        if retrieval_strategy == RetrievalStrategy.SEMANTIC:
            lc_documents = semantic_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.FULL_TEXT:
            lc_documents = full_text_retriever.invoke(query)[:k]
        else:
            lc_documents = hybrid_retriever.invoke(query)[:k]
        # 知识库查询记录 存储唯一记录
        unique_dataset_ids = list(set(str(lc_document.metadata["dataset_id"]) for lc_document in lc_documents))
        for dataset_id in unique_dataset_ids:
            self.create(
                DatasetQuery,
                dataset_id=dataset_id,
                query=query,
                source=retrival_source,
                # todo:等待APP配置模块完成后进行调整
                source_app_id=None,
                created_by=account_id,
            )

        # 更新片段的命中次数 召回次数
        with self.db.auto_commit():
            stmt = (
                update(Segment)
                .where(Segment.id.in_([lc_document.metadata["segment_id"] for lc_document in lc_documents]))
                .values(hit_count=Segment.hit_count + 1)
            )
            self.db.session.execute(stmt)

        return lc_documents
