# !/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   document_handler
@Time   :   2025/12/22 20:54
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from injector import inject

from internal.schema.document_schema import CreateDocumentReq, CreateDocumentResp, GetDocumentsWithPageReq, \
    GetDocumentsWithPageResp, GetDocumentResp, UpdateDocumentNameReq, UpdateDocumentEnabledReq
from internal.service import DocumentService
from pkg.paginator import PageModel
from pkg.response import success_json, validate_error_json, success_message


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

    def get_documents_with_page(self, dataset_id: UUID):
        """获取指定知识库的文档分页列表"""
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        documents, paginator = self.document_service.get_documents_with_page(dataset_id, req)

        resp = GetDocumentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(documents), paginator=paginator))

    def get_document(self, dataset_id: UUID, document_id: UUID):
        """获取指定知识库下指定文档基础信息"""
        document = self.document_service.get_document(dataset_id, document_id)
        resp = GetDocumentResp()
        return success_json(resp.dump(document))

    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        """更新指定知识库下指定文档的名称"""
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_name(dataset_id, document_id, name=req.name.data)
        return success_message("更新文档名称成功")

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID):
        """更新指定知识库下指定文档启用状态"""
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_enabled(dataset_id, document_id, enabled=req.enabled.data)
        return success_message("更新文档启用状态成功")

    def delete_document(self, dataset_id: UUID, document_id: UUID):
        self.document_service.delete_document(dataset_id, document_id)
        """删除指定知识库下指定文档"""
        return success_message("删除文档成功")

    def get_documents_status(self, dataset_id: UUID, batch: str):
        """根据批处理标识获取文档处理进度"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch)
        return success_json(documents_status)
