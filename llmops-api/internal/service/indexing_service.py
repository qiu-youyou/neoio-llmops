#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   indexing_service
@Time   :   2025/12/22 22:22
@Author :   s.qiu@foxmail.com
"""
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from flask import Flask, current_app
from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import func
from weaviate.classes.query import Filter

from internal.core.file_extractor import FileExtractor
from internal.entity.cache_entity import LOCK_DOCUMENT_UPDATE_ENABLED
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.exception import NotFoundException
from internal.lib.helper import generate_text_hash
from internal.model import Document, Segment, KeywordTable, DatasetQuery
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .process_rule_service import ProcessRuleService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class IndexingService(BaseService):
    """索引构建服务"""
    db: SQLAlchemy
    redis_client: Redis
    file_extractor: FileExtractor
    embeddings_service: EmbeddingsService
    process_rule_service: ProcessRuleService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService
    jieba_service: JiebaService

    def build_documents(self, document_ids: list[UUID]) -> None:
        """根据文档id列表 构建知识库文档 涵盖加载、分割、索引构建、存储等"""

        # 获取所有文档
        documents = self.db.session.query(Document).filter(Document.id.in_(document_ids)).all()

        # 遍历处理每一个文档
        for document in documents:
            try:
                # 更改改状态为解析中
                self.update(document, status=DocumentStatus.PARSING, processing_started_at=datetime.now())

                # 执行文档加载步骤，并更新文档的状态与时间
                lc_documents = self._parsing(document)

                # 执行文档分割步骤，片段的信息，更新文档状态
                lc_segments = self._splitting(document, lc_documents)

                # 执行索引构建、关键词提取
                self._indexing(document, lc_segments)

                # 执行存储操作 更新文档状态 存储到向量数据库
                self._completed(document, lc_segments)

            except Exception as e:
                # 更改状态为失败 并记录日志
                logging.exception(f"构建文档发生错误，错误信息为：{str(e)}")
                self.update(document, status=DocumentStatus.ERROR, error=str(e), stopped_at=datetime.now())

        return "根据文档id列表 构建文档"

    def update_document_enabled(self, document_id: UUID) -> None:
        """更新指定文档状态，同步关键词 片段 向量等修改"""
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)
        document = self.get(Document, document_id)
        if document is None:
            logging.exception(f"当前文档不存在：{document_id}")
            raise NotFoundException("当前文档不存在")
        # 查询当前文档的所有片段
        segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.node_id, Segment.enabled).filter(
            Segment.document_id == document_id, Segment.status == SegmentStatus.COMPLETED).all()
        node_ids = [node_id for _, node_id, _ in segments]

        # 遍历 node_ids 更新对应的向量数据库
        try:
            collection = self.vector_database_service.collection
            for node_id in node_ids:
                try:
                    collection.data.update(uuid=node_id, properties={"document_enabled": document.enabled})
                except Exception as e:
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(Segment.node_id == node_id).update(
                            {
                                "error": str(e),
                                "status": SegmentStatus.ERROR,
                                "enabled": False,
                                "disabled_at": datetime.now(),
                                "stopped_at": datetime.now(),
                            }
                        )

            # 更新关键词表中的数据
            if document.enabled is True:
                # 从禁用改为启用需要 新增关键词
                enabled_segment_ids = [id for id, _, enabled in segments if enabled is True]
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id=document.dataset_id,
                                                                      segment_ids=enabled_segment_ids)
            else:
                # 从启用改为禁用 需要剔除相关关键词
                segment_ids = [id for id, _, _ in segments]
                self.keyword_table_service.delete_keyword_table_from_ids(dataset_id=document.dataset_id,
                                                                         segment_ids=segment_ids)
        except Exception as e:
            # 记录失败日志并回退状态
            logging.exception(f"更改向量数据库文档启用状态失败，文档ID{document_id}，错误信息：{str(e)}")
            origin_enabled = not document.enabled
            self.update(document, enabled=origin_enabled, disabled_at=None if origin_enabled else datetime.now())
        finally:
            # 任务完成后清空缓存键
            self.redis_client.delete(cache_key)

    def delete_document(self, dataset_id: UUID, document_id: UUID) -> None:
        """删除指定文档，同步关键词 片段 向量等修改"""
        # 查找文档下的所有片段 ID 列表
        segment_ids = self.db.session.query(Segment).with_entities(Segment.id).filter(
            Segment.document_id == document_id).all()

        # 删除向量数据库中对应的数据
        collection = self.vector_database_service.collection
        collection.data.delete_many(where=Filter.by_property("document_id").equal(document_id))

        # 删除Postgres数据库的 segment 记录
        with self.db.auto_commit():
            self.db.session.query(Segment).filter(Segment.document_id == document_id).delete()

        # 更新片段对应的关键词表记录
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, segment_ids)

    def delete_dataset(self, dataset_id: UUID) -> None:
        """删除指定知识库 包含知识库下所有 文档、片段、关键词表、相关向量数据"""

        try:
            with self.db.auto_commit():
                # 删除关联的文档
                self.db.session.query(Document).filter(Document.dataset_id == dataset_id).delete()
                # 删除关联的片段
                self.db.session.query(Segment).filter(Segment.dataset_id == dataset_id).delete()
                # 删除关联的关键词
                self.db.session.query(KeywordTable).filter(KeywordTable.dataset_id == dataset_id).delete()
                # 删除最近查询记录
                self.db.session.query(DatasetQuery).filter(DatasetQuery.dataset_id == dataset_id).delete()

            # 删除向量数据库中关联的数据
            self.vector_database_service.collection.data.delete_many(
                where=Filter.by_property("dataset_id").equal(str(dataset_id))
            )

        except Exception as e:
            logging.exception(f"知识库删除异步任务出错，dataset_id: {dataset_id}，错误信息：{str(e)}")

    def _parsing(self, document: Document) -> list[LCDocument]:
        """解析传递的文档为LangChain文档列表"""
        upload_file = document.upload_file
        lc_documents = self.file_extractor.load(upload_file)
        # 删除多余的空白字符串
        for lc_document in lc_documents:
            lc_document.page_content = self._clean_extra_text(lc_document.page_content)

        # 更新文档状态并记录时间
        self.update(
            document,
            character_count=sum([len(lc_document.page_content) for lc_document in lc_documents]),
            status=DocumentStatus.SPLITTING,
            parsing_completed_at=datetime.now(),
        )

        return lc_documents

    def _splitting(self, document: Document, lc_documents: list[LCDocument]) -> list[LCDocument]:
        """文档分割 拆分为小块片段"""

        process_rule = document.process_rule

        # 根据 process_rule 规则清除多余的字符串
        for lc_document in lc_documents:
            lc_document.page_content = self.process_rule_service.clean_text_by_process_rule(
                lc_document.page_content,
                process_rule,
            )

        # 根据process_rule获取文本分割器
        text_splitter = self.process_rule_service.get_text_splitter_by_process_rule(
            process_rule,
            self.embeddings_service.calculate_token_count
        )

        # 分割文档列表为片段列表
        lc_segments = text_splitter.split_documents(lc_documents)

        # 定位到当前文档下的最大片段位置
        position = self.db.session.query((func.coalesce(func.max(Segment.position), 0))).filter(
            Segment.document_id == document.id
        ).scalar()

        # 遍历分割文档  存入片段数据
        segments = []
        for lc_segment in lc_segments:
            position += 1
            content = lc_segment.page_content
            segment = self.create(
                Segment,
                account_id=document.account_id,
                dataset_id=document.dataset_id,
                document_id=document.id,
                node_id=uuid.uuid4(),
                position=position,
                content=content,
                character_count=len(content),
                token_count=self.embeddings_service.calculate_token_count(content),
                status=SegmentStatus.WAITING,
                hash=generate_text_hash(content),
            )
            # 添加元数据
            lc_segment.metadata = {
                "account_id": str(document.account_id),
                "dataset_id": str(document.dataset_id),
                "document_id": str(document.id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": False,
                "segment_enabled": False,
            }
            segments.append(segment)

        # 更新文档的数据，涵盖状态、token数等内容
        self.update(
            document,
            status=DocumentStatus.INDEXING,
            splitting_completed_at=datetime.now(),
            token_count=sum([segment.token_count for segment in segments]),
        )

        return lc_segments

    def _indexing(self, document: Document, lc_segments: list[LCDocument]) -> None:
        """构建文档索引 提取关键词、词表构建"""

        for lc_segment in lc_segments:
            keywords = self.jieba_service.extract_keywords(lc_segment.page_content, 10)
            # 更新文档片段keywords
            self.db.session.query(Segment).filter(Segment.id == lc_segment.metadata["segment_id"]).update({
                "keywords": keywords,
                "status": SegmentStatus.INDEXING,
                "indexing_completed_at": datetime.now(),
            })

            # 当前知识库的关键词表更新
            keyword_table_record = self.keyword_table_service.get_keyword_table_from_dataset_id(document.dataset_id)
            keyword_table = {field: set(value) for field, value in keyword_table_record.keyword_table.items()}
            for keyword in keywords:
                if keyword not in keyword_table:
                    keyword_table[keyword] = set()
                keyword_table[keyword].add(lc_segment.metadata["segment_id"])
            self.update(keyword_table_record,
                        keyword_table={field: list(value) for field, value in keyword_table.items()})

        # 更新文档状态
        self.update(document, indexing_completed_at=datetime.now())

    def _completed(self, document: Document, lc_segments: list[LCDocument]) -> None:
        """文档片段存储到向量数据库，文档状态已完成"""
        for lc_segment in lc_segments:
            lc_segment.metadata["document_enabled"] = True
            lc_segment.metadata["segment_enabled"] = True

        # 向量存储 每次10条
        def thread_func(flask_app: Flask, chunks: list[LCDocument], ids: list[UUID]) -> list[UUID]:
            """线程函数 执行 postgress 与向量存储"""
            try:
                with flask_app.app_context():
                    # todo: 暂时不进行向量数据库的存储
                    self.vector_database_service.vector_store.add_documents(chunks, ids=ids)
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(Segment.node_id.in_(ids)).update({
                            "status": SegmentStatus.COMPLETED,
                            "completed_at": datetime.now(),
                            "enabled": True,
                        })
            except Exception as e:
                logging.exception(f"构建文档片段索引发生异常，错误信息 {str(e)}")
                with self.db.auto_commit():
                    self.db.session.query(Segment).filter(Segment.node_id.in_(ids)).update({
                        "status": SegmentStatus.ERROR,
                        "completed_at": None,
                        "stopped_at": datetime.now(),
                        "enabled": False,
                    })

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(0, len(lc_segments), 10):
                chunks = lc_segments[i: i + 10]
                ids = [chunk.metadata["node_id"] for chunk in chunks]
                futures.append(executor.submit(thread_func, current_app._get_current_object(), chunks, ids))

            for future in futures:
                future.result()

        # 更新文档状态
        self.update(
            document,
            status=DocumentStatus.COMPLETED,
            completed_at=datetime.now(),
            enabled=True,
        )

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 删除零宽非标记字符
        return text
