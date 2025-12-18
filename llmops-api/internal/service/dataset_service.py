#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_service
@Time   :   2025/12/18 13:41
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateErrorException
from internal.model import Dataset
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq
from internal.service.base_service import BaseService
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""
    db: SQLAlchemy

    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        """创建知识库"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 该账号下是否有同名的知识库
        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account_id,
            name=req.name.data
        ).one_or_none()

        if dataset:
            raise ValidateErrorException(f"该知识库{req.name.data}已存在")

        # 没有描述信息使用默认值
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        return self.create(Dataset,
                           account_id=account_id,
                           name=req.name.data,
                           icon=req.icon.data,
                           description=req.description.data)

    def update_dataset(self, req: UpdateDatasetReq, dataset_id: UUID) -> Dataset:
        """更新知识库"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 该数据是否存在
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ValidateErrorException("该知识库不存在")

        # 该账号下是否有同名的知识库
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account_id,
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

    def get_dataset(self, dataset_id: UUID) -> Dataset:
        """获取指定知识库信息"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 该数据是否存在
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ValidateErrorException("该知识库不存在")

        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq) -> tuple[list[Dataset], Paginator]:
        """获取知识库分页列表数据"""
        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 构建筛选器 分页查询器
        paginator = Paginator(db=self.db, req=req)
        filters = [Dataset.account_id == account_id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at")),
        )

        return datasets, paginator
