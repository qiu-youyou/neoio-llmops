#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   upload_file_service
@Time   :   2025/12/16 10:10
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from injector import inject

from internal.model.upload_file import UploadFile
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class UploadFileService(BaseService):
    """上传文件记录服务"""
    db: SQLAlchemy

    def create_upload_file(self, **kwargs) -> UploadFile:
        """创建文件上传记录"""
        return self.create(UploadFile, **kwargs)
