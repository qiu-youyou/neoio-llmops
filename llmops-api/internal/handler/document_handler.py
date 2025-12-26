#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   document_handler
@Time   :   2025/12/22 20:54
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.document_schema import CreateDocumentReq, CreateDocumentResp
from internal.service import DocumentService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class DocumentHandler:
    """文档处理器"""
    document_service: DocumentService

    def create_documents(self, dataset_id: UUID):
        """知识库上传文档列表"""
        req = CreateDocumentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务并创建文档 返回文档列表+处理批次
        document, batch = self.document_service.create_documents(dataset_id, **req.data)

        resp = CreateDocumentResp()
        return success_json(resp.dump((document, batch)))

    def get_documents_status(self, dataset_id: UUID, batch: str):
        """根据批处理标识获取文档处理进度"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch)
        return success_json(documents_status)
