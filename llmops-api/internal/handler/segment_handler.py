#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   segment_handler
@Time   :   2026/1/6 15:46
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.segment_schema import CreateSegmentReq, GetSegmentsWithPageReq, GetSegmentsWithPageResp, \
    GetSegmentResp, UpdateSegmentReq, UpdateSegmentEnabledReq
from internal.service import SegmentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class SegmentHandler:
    segment_service: SegmentService
    """片段处理器"""

    def get_segments_with_page(self, dataset_id: UUID, document_id: UUID):
        """获取指定知识库文档的片段列表"""
        req = GetSegmentsWithPageReq()
        if not req.validate():
            raise validate_error_json(req.errors)

        segments, paginator = self.segment_service.get_segments_with_page(dataset_id, document_id, req)
        resp = GetSegmentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(segments), paginator=paginator))

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """获取指定知识库文档的片段信息"""
        segment = self.segment_service.get_segment(dataset_id, document_id, segment_id)
        resp = GetSegmentResp()
        return success_json(resp.dump(segment))

    def create_segment(self, dataset_id: UUID, document_id: UUID):
        """指定知识库的文档下新增片段信息"""
        # 提取请求并校验
        req = CreateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.create_segment(dataset_id, document_id, req)
        return success_json("新增文档片段成功")

    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """指定知识库的文档下更新片段信息"""
        req = UpdateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.update_segment(dataset_id, document_id, segment_id, req)
        return success_json("更新文档片段成功")

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """更新指定知识库文档下指定片段的启用状态"""
        req = UpdateSegmentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.update_segment_enabled(dataset_id, document_id, segment_id, req.enabled.data)
        return success_message("更新文档片段成功")

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID):
        """删除知识库文档下指定片段"""
        self.segment_service.delete_segment(dataset_id, document_id, segment_id)
        return success_message("删除文档片段成功")
