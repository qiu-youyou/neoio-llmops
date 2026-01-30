#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   upload_file_handler
@Time   :   2025/12/16 09:29
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from flask_login import current_user, login_required
from injector import inject

from internal.schema.upload_file_schema import UploadFileReq, UploadFileResp, UploadImageReq
from internal.service.cos_service import CosService
from pkg.response import validate_error_json, success_json


@inject
@dataclass
class UploadFileHandler:
    """上传文件处理器"""
    cos_service: CosService

    @login_required
    def upload_file(self):
        """上传文件"""
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)
        upload_file = self.cos_service.upload_file(req.file.data, False, current_user)
        resp = UploadFileResp()

        # 调用上传服务
        return success_json(resp.dump(upload_file))

    @login_required
    def upload_image(self):
        """上传图片"""
        req = UploadImageReq()
        if not req.validate():
            return validate_error_json(req.errors)
        upload_file = self.cos_service.upload_file(req.file.data, True, current_user)
        # 图片预览地址
        image_url = self.cos_service.get_file_url(upload_file.key)
        return success_json({"image_url": image_url})
