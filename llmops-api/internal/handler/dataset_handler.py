#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_handler
@Time   :   2025/12/18 11:45
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from injector import inject


@inject
@dataclass
class DatasetHandler:
    """知识库处理器"""

    def create_dataset(self):
        """创建知识库"""

    def get_dataset(self, dataset_id: UUID):
        """根据知识库id查询"""

    def update_dataset(self, dataset_id: UUID):
        """知识库id+信息 更新知识库"""

    def get_datasets_with_page(self):
        """获取知识库分页+搜索列表数据"""
