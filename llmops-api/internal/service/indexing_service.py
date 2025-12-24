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
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from sqlalchemy import func

from internal.core.file_extractor import FileExtractor
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.model import Document, Segment
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .process_rule_service import ProcessRuleService
from ..lib.helper import generate_text_hash


@inject
@dataclass
class IndexingService(BaseService):
    """索引构建服务"""
    db: SQLAlchemy
    file_extractor: FileExtractor
    embeddings_service: EmbeddingsService
    process_rule_service: ProcessRuleService

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

            except Exception as e:
                # 更改状态为失败 并记录日志
                logging.exception(f"构建文档发生错误，错误信息为：{str(e)}")
                self.update(document, status=DocumentStatus.ERROR, error=str(e), stopped_at=datetime.now())

        return "根据文档id列表 构建文档"

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

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 删除零宽非标记字符
        return text
