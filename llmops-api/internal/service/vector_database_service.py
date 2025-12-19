#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   vector_database_service
@Time   :   2025/12/19 09:03
@Author :   s.qiu@foxmail.com
"""
import os

import weaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient

from .embeddings_service import EmbeddingsService


@inject
class VectorDatabaseService:
    """向量数据库服务"""
    client: WeaviateClient
    vector_store: WeaviateVectorStore
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        """langChain 向量数据库创建"""
        self.embeddings_service = embeddings_service

        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            grpc_port=os.getenv("WEAVIATE_PORT"),
        )

        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name="Dataset",
            text_key="text",
            embedding=self.embeddings_service.embeddings
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @classmethod
    def combine_documents(cls, documents: list[Document]) -> str:
        return "\n\n".join([document.page_content for document in documents])
