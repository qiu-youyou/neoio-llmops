#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   document_service
@Time   :   2025/12/22 21:05
@Author :   s.qiu@foxmail.com
"""
import logging
import random
import time
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.entity.dataset_entity import ProcessType
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION
from internal.exception import ForbiddenException, FailException
from internal.model import Document, Dataset, UploadFile, ProcessRule
from internal.service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DocumentService(BaseService):
    """文档服务"""
    db: SQLAlchemy

    def create_documents(self,
                         dataset_id: UUID,
                         upload_file_ids: list[UUID],
                         process_type: str = ProcessType.AUTOMATIC,
                         rule: dict = None
                         ) -> tuple[list[Document], str]:
        """创建文档列表 调用异步任务"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account_id:
            raise ForbiddenException("知识库不存在或无权限")

        # 提取文件并校验文件权限与扩展
        upload_files = self.db.session.query(UploadFile).filter(
            UploadFile.account_id == account_id,
            UploadFile.id.in_(upload_file_ids)
        ).all()

        # 保存允许处理的类型
        upload_files = [upload_file for upload_file in upload_files if
                        upload_file.extension.lower() in ALLOWED_DOCUMENT_EXTENSION]

        if len(upload_files) == 0:
            logging.warning(
                f"上传文档列表未解析到合法文件，account_id: {account_id}, dataset_id: {dataset_id}, upload_file_ids: {upload_file_ids}")
            raise FailException("未解析到合法文件")

        # 创建批次与处理规则并记录数据库
        batch = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100000, 999999))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule,
        )

        # 获取档期知识库最新文档的位置

        # 遍历所有合法的上传文件列表并记录数据

        # 调用异步任务，完成后续操作

        # 返回文档列表与处理批次
        # return doucments, batch

        def get_latest_document_position(self, dataset_id: UUID) -> int:
            """获取该知识库最新文档位置"""
