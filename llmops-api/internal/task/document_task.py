#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   document_task
@Time   :   2025/12/22 22:20
@Author :   s.qiu@foxmail.com
"""
from uuid import UUID

from celery import shared_task


@shared_task
def build_documents(document_ids: list[UUID]) -> None:
    """根据传递额文档id列表 构建文档"""

    # todo:::
    # 根据传递的文档id获取所有文档

    # 遍历所有文档完成对每个文档的构建
