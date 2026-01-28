#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_handler
@Time   :   2025/12/18 11:45
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from flask_login import login_required, current_user
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetResp, GetDatasetsWithPageReq, \
    GetDatasetsWithPageResp, HitReq, GetDatasetQueriesResp
from internal.service import DatasetService, JiebaService, VectorDatabaseService
from pkg.paginator import PageModel
from pkg.response import success_message, validate_error_json, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    """知识库处理器"""
    db: SQLAlchemy
    file_extractor: FileExtractor
    dataset_service: DatasetService
    vector_database_service: VectorDatabaseService
    jieba_service: JiebaService

    def create_dataset(self):
        """创建知识库"""
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.create_dataset(req)
        return success_message("知识库创建成功")

    @login_required
    def get_dataset(self, dataset_id: UUID):
        """根据知识库id获取详情"""
        dataset = self.dataset_service.get_dataset(dataset_id, current_user)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: UUID):
        """知识库id+信息 更新知识库"""
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.update_dataset(req, dataset_id)
        return success_message("知识库更新成功")

    @login_required
    def get_datasets_with_page(self):
        """获取知识库分页+搜索列表数据"""
        req = GetDatasetsWithPageReq()
        if not req.validate():
            return validate_error_json(req.errors)
        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

    def get_dataset_queries(self, dataset_id: UUID):
        """"根据传递的知识库获取最近10条查询记录"""
        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id)
        resp = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))

    def delete_dataset(self, dataset_id: UUID):
        """删除知识库"""
        self.dataset_service.delete_dataset(dataset_id)
        return success_message("删除成功")

    def hit(self, dataset_id: UUID):
        """指定知识库 召回测试"""
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 调用服务执行检索策略
        hit_result = self.dataset_service.hit(dataset_id, req)
        return success_json(hit_result)
