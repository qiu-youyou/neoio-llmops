#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   segment_service
@Time   :   2026/1/6 15:53
@Author :   s.qiu@foxmail.com
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import func, asc

from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.exception import ValidateErrorException, FailException, NotFoundException
from internal.lib.helper import generate_text_hash
from internal.model import Segment, Document, Account
from internal.schema.segment_schema import CreateSegmentReq, UpdateSegmentReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService
from ..entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME


@inject
@dataclass
class SegmentService(BaseService):
    """片段处理服务"""
    db: SQLAlchemy
    redis_client: Redis
    jieba_service: JiebaService
    embeddings_service: EmbeddingsService
    vector_database_service: VectorDatabaseService
    keyword_table_service: KeywordTableService

    def get_segments_with_page(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq, account: Account
                               ) -> tuple[list[Segment], Paginator]:
        """获取指定知识库文档的片段列表"""

        # 校验文档是否存在 是否有权限操作
        document = self.get(Document, document_id)
        if document is None or document.account_id != account.id or document.dataset_id != dataset_id:
            raise NotFoundException("文档片段不存在或无权限！")

        paginate = Paginator(self.db, req=req)
        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        segments = paginate.paginate(self.db.session.query(Segment).filter(*filters).order_by(asc("position")))
        return segments, paginate

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """获取指定知识库文档的片段信息"""

        # 校验文档是否存在 是否有权限操作
        segment = self.get(Segment, segment_id)
        if (segment is None or
                segment.account_id != account.id or segment.dataset_id != dataset_id or segment.document_id != document_id):
            raise NotFoundException("文档片段不存在或无权限！")

        return segment

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq, account: Account) -> Segment:
        """指定知识库的文档下新增片段"""

        # 上传的 content 内容不能超过 1000 个 tokens
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateErrorException("内容最大长度不能超过 1000 tokens")

        # 校验文档是否存在 是否有权限操作
        document = self.get(Document, document_id)
        if document is None or document.account_id != account.id or document.dataset_id != dataset_id:
            raise NotFoundException("文档片段不存在或无权限！")

        # 只有状态为 complete 的文档可以进行操作
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("当前文档状态不能新增片段")

        # 获取当前文档片段的最大位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id).scalar()

        # 如果没有传递 keywords 则根据 content 生成关键词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 数据库新增数据位置+1
        segment = None
        try:
            position += 1  # 位置+1
            segment = self.create(Segment, account_id=account.id,
                                  dataset_id=dataset_id,
                                  document_id=document_id,
                                  node_id=uuid.uuid4(),
                                  position=position,
                                  content=req.content.data,
                                  character_count=len(req.content.data),
                                  token_count=token_count,
                                  keywords=req.keywords.data,
                                  hash=generate_text_hash(req.content.data),
                                  enabled=True,
                                  processing_started_at=datetime.now(),
                                  indexing_completed_at=datetime.now(),
                                  completed_at=datetime.now(),
                                  status=SegmentStatus.COMPLETED)

            # 向量数据库新增数据
            self.vector_database_service.vector_store.add_documents([
                LCDocument(page_content=req.content.data,
                           metadata={
                               "account_id": str(document.account_id),
                               "dataset_id": str(document.dataset_id),
                               "document_id": str(document.id),
                               "segment_id": str(segment.id),
                               "node_id": str(segment.node_id),
                               "document_enabled": document.enabled,
                               "segment_enabled": True,
                           })],
                ids=[str(segment.node_id)])

            # 更新文档的 字符总数 以及 token 数
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0)
            ).first()
            self.update(document, character_count=document_character_count, token_count=document_token_count)

            # 更新知识库的关键词表信息
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, segment_ids=[str(segment.id)])

        except Exception as e:
            logging.exception(f"新增文档片段一场，错误信息：{str(3)}")
            if segment:
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
            raise FailException("新增文档片段失败")

    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, req: UpdateSegmentReq,
                       account: Account) -> Segment:
        """指定知识库的文档下更新片段信息"""

        # 上传的 content 内容不能超过 1000 个 tokens
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateErrorException("内容最大长度不能超过 1000 tokens")

        # 校验文档是否存在 是否有权限操作
        segment = self.get(Segment, segment_id)
        if (segment is None or
                segment.account_id != account.id or segment.dataset_id != dataset_id or segment.document_id != document_id):
            raise NotFoundException("片段不存在或无权限！")

        # 只有状态为 complete 的文档可以进行操作
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前片段状态不能更新")

        # 如果没有传递 keywords 则根据 content 生成关键词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 计算hash判断是否需要更新向量数据库及文档
        new_hash = generate_text_hash(req.content.data)
        required_update = segment.hash != new_hash

        # 更新片段信息
        try:
            self.update(segment,
                        keywords=req.keywords.data,
                        content=req.content.data,
                        hash=new_hash,
                        character_count=len(req.content.data),
                        token_count=self.embeddings_service.calculate_token_count(req.content.data))
            self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])
            # 是否更新文档及向量
            if required_update:
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0),
                ).first()
                self.update(document, character_count=document_character_count, token_count=document_token_count)
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={"text": req.content.data},
                    vector=self.embeddings_service.embeddings.embed_query(req.content.data)
                )
        except Exception as e:
            logging.exception(f"更新文档片段失败，segment_id={segment.id}，错误信息{str(e)}")
            raise FailException("更新文档片段失败")

        return segment

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID,
                               enabled: bool, account: Account) -> Segment:
        """更新指定知识库文档下指定片段的启用状态"""

        # 校验文档是否存在 是否有权限操作
        segment = self.get(Segment, segment_id)
        if (segment is None or
                segment.account_id != account.id or segment.dataset_id != dataset_id or segment.document_id != document_id):
            raise NotFoundException("片段不存在或无权限！")

        # 只有状态为 complete 的文档可以进行操作
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前片段状态不能更新")
        if enabled == segment.enabled:
            raise FailException(f"片段状态修改错误，当前已是{'启用' if enabled else '禁用'}")

        # 获取更新片段启用状态锁并上锁检测
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("当前片段正在修改，请稍后重试！")

        # 上锁并更新对应的数据以及向量数据、关键词表
        with self.redis_client.lock(cache_key, LOCK_EXPIRE_TIME):
            try:
                # 修改 postgres 片段状态 禁用要记录禁用时间
                self.update(segment, enabled=enabled, disabled_at=None if enabled else datetime.now())
                # 更新对应关键词表信息 根据状态判断
                document = segment.document
                if document.enabled is True and enabled is True:
                    self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
                # 更新向量数据库该条数据状态
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id, properties={"segment_enabled": enabled})
            except Exception as e:
                logging.exception(f"更改片段启用状态失败，segment_id:{segment_id}，错误信息：{str(e)}")
                self.update(segment,
                            error=str(e),
                            enabled=False,
                            status=SegmentStatus.ERROR,
                            disabled_at=datetime.now(),
                            stopped_at=datetime.now())
                raise FailException("更新文档片段状态失败")

        return segment

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """删除知识库文档下指定片段"""

        # 校验文档是否存在 是否有权限操作
        segment = self.get(Segment, segment_id)
        if (segment is None or
                segment.account_id != account.id or segment.dataset_id != dataset_id or segment.document_id != document_id):
            raise NotFoundException("片段不存在或无权限！")

        # 只有 完成/错误 状态的文档可以被删除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("文档片段处于不可删除状态")

        # 删除片段、关键词
        document = segment.document
        self.delete(segment)
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(f"删除片段失败，segment_id:{segment_id}，错误信息：{str(e)}")

        # 更新文档、重新计算 字符数、token数
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0),
        ).first()
        self.update(document, character_count=document_character_count, token_count=document_token_count)

        return segment
