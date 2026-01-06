#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   segment_service
@Time   :   2026/1/6 15:53
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.model import Segment
from internal.schema.segment_schema import CreateSegmentReq
from internal.service import BaseService


@inject
@dataclass
class SegmentService(BaseService):
    """片段处理服务"""

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq) -> Segment:
        """指定知识库的文档下新增片段"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 上传的 content 内容不能超过 1000 个 tokens
        # 校验文档是否存在 是否有权限操作
        # 只有状态为 complete 的文档可以进行操作

        # 获取当前文档片段的最大位置
        # 如果没有传递 keywords 则根据 content 生成关键词

        # 数据库新增数据
        # 向量数据库新增数据
        # 更新文档的 字符总数 以及 token 数
        # 更新知识库的关键词表信息
