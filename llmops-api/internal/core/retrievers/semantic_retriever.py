#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   semantic_retriever
@Time   :   2026/1/19 10:08
@Author :   s.qiu@foxmail.com
"""
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from langchain_weaviate import WeaviateVectorStore
from pydantic import Field
from weaviate.classes.query import Filter


class SemanticRetriever(BaseRetriever):
    """相似性/向量 检索器"""
    dataset_ids: list[UUID]
    vector_store: WeaviateVectorStore
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        """query 执行相似性检索"""

        # 最大搜索条件 k 默认 4
        k = self.search_kwargs["k"]

        # 执行相似性检索并获取得分
        search_result = self.vector_store.similarity_search_with_relevance_scores(
            query,
            **{
                "filters": Filter.all_of([
                    Filter.by_property("dataset_id").contains_any([str(dataset_id) for dataset_id in self.dataset_ids]),
                    Filter.by_property("document_enabled").equal(True),
                    Filter.by_property("segment_enabled").equal(True)
                ]),
                **self.search_kwargs
            }
        )

        if search_result is None or len(search_result) == 0:
            return []
        lc_documents, scores = zip(*search_result)

        # 将得分添加到 文档元数据中
        for lc_document, score in zip(lc_documents, scores):
            lc_document.metadata["score"] = score

        return list(lc_documents)
