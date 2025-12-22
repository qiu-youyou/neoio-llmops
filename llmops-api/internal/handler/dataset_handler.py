#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_handler
@Time   :   2025/12/18 11:45
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from flask import request
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetResp, GetDatasetsWithPageReq, \
    GetDatasetsWithPageResp
from internal.service import EmbeddingsService
from internal.service.dataset_service import DatasetService
from internal.service.jieba_service import JiebaService
from pkg.paginator import PageModel
from pkg.response import success_message, validate_error_json, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    """知识库处理器"""
    file_extractor: FileExtractor
    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    db: SQLAlchemy

    def create_dataset(self):
        """创建知识库"""
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.create_dataset(req)
        return success_message("知识库创建成功")

    def get_dataset(self, dataset_id: UUID):
        """根据知识库id获取详情"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: UUID):
        """知识库id+信息 更新知识库"""
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.update_dataset(req, dataset_id)
        return success_message("知识库更新成功")

    def get_datasets_with_page(self):
        """获取知识库分页+搜索列表数据"""
        req = GetDatasetsWithPageReq()
        if not req.validate():
            return validate_error_json(req.errors)
        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

    def embeddings_query(self):
        """测试 embedding"""
        query = request.args.get("query")
        keywords = self.jieba_service.extract_keywords(query)
        return success_json({"keywords": keywords})
        # upload_file = self.db.session.query(UploadFile).get("7d2f59b8-6e9e-432e-ad0c-a46685280f87")
        # content = self.file_extractor.load(upload_file, True)
        # return success_json({"content": content})
