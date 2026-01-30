#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_service
@Time   :   2025/12/18 13:41
@Author :   s.qiu@foxmail.com
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateErrorException, NotFoundException, FailException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset, Segment, DatasetQuery, AppDatasetJoin, Account
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq, HitReq
from internal.service.base_service import BaseService
from internal.service.indexing_service import IndexingService
from internal.service.retrieval_service import RetrievalService
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""
    db: SQLAlchemy
    retrieval_service: RetrievalService
    indexing_service: IndexingService

    def create_dataset(self, req: CreateDatasetReq, account: Account) -> Dataset:
        """创建知识库"""

        # 该账号下是否有同名的知识库
        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account.id,
            name=req.name.data
        ).one_or_none()

        if dataset:
            raise ValidateErrorException(f"该知识库{req.name.data}已存在")

        # 没有描述信息使用默认值
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        return self.create(Dataset,
                           account_id=account.id,
                           name=req.name.data,
                           icon=req.icon.data,
                           description=req.description.data)

    def update_dataset(self, req: UpdateDatasetReq, dataset_id: UUID, account: Account) -> Dataset:
        """更新知识库"""

        # 该数据是否存在
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 该账号下是否有同名的知识库
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account.id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id,
        ).one_or_none()

        if check_dataset:
            raise ValidateErrorException(f"该知识库名称{req.name.data}已存在")

        # 没有描述信息使用默认值
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        self.update(dataset,
                    name=req.name.data,
                    icon=req.icon.data,
                    description=req.description.data)
        return dataset

    def get_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """获取指定知识库信息"""
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")
        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq, account: Account) -> tuple[list[Dataset], Paginator]:
        """获取知识库分页列表数据"""

        # 构建筛选器 分页查询器
        filters = [Dataset.account_id == account.id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        paginator = Paginator(self.db, req)
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at")),
        )
        return datasets, paginator

    def delete_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """删除该知识库 涵盖知识库下所有 文档、片段、关键词表、对应向量数据库"""

        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在")

        try:
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(AppDatasetJoin.dataset_id == dataset_id).delete()

            # 异步任务执行后续操作
            self.indexing_service.delete_dataset(dataset_id)

        except Exception as e:
            logging.exception(f"删除知识库失败, dataset_id: {dataset_id}, 错误信息: {str(e)}")
            raise FailException("删除知识库失败")

    def get_dataset_queries(self, dataset_id: UUID, account: Account) -> list[DatasetQuery]:
        """获取当前知识库最新查询的10条记录"""

        datset = self.get(Dataset, dataset_id)
        if datset is None or datset.account_id != account.id:
            raise NotFoundException("知识库不存在")

        dataset_queries = self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id).order_by(desc("created_at")).limit(10).all()

        return dataset_queries

    def hit(self, dataset_id: UUID, req: HitReq, account: Account) -> list[dict]:
        """指定知识库 召回测试"""

        # 知识库是否存在
        dateset = self.get(Dataset, dataset_id)
        if dateset is None or dateset.account_id != account.id:
            raise NotFoundException("知识库不存在")

        # 执行检索
        lc_documents = self.retrieval_service.search_in_datasets(dataset_ids=[dataset_id], **req.data)
        lc_document_dict = {str(lc_document.metadata["segment_id"]): lc_document for lc_document in lc_documents}

        # 根据检索数据查询对应片段信息
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([str(lc_document.metadata["segment_id"]) for lc_document in lc_documents])
        ).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 片段数据排序
        sorted_segments = [
            segment_dict[str(lc_document.metadata["segment_id"])]
            for lc_document in lc_documents
            if str(lc_document.metadata["segment_id"]) in segment_dict
        ]

        # 组装数据
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                },
                "dataset_id": segment.dataset_id,
                "score": lc_document_dict[str(segment.id)].metadata["score"],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result
