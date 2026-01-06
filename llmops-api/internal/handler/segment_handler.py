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

from internal.schema.segment_schema import CreateSegmentReq
from internal.service import SegmentService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class SegmentHandler:
    segment_service: SegmentService
    """片段处理器"""

    def create_segment(self, dataset_id: UUID, document_id: UUID):
        """指定知识库的文档下新增片段"""
        # 提取请求并校验
        req = CreateSegmentReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.segment_service.create_segment(dataset_id, document_id, req)
        return success_json("新增文档片段成功")

    def get_segments_with_page(self, dataset_id: UUID, document_id: UUID, ):
        """获取指定知识库文档的片段列表"""
