#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   cos_service
@Time   :   2025/12/16 09:56
@Author :   s.qiu@foxmail.com
"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from injector import inject
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOWED_IMAGE_EXTENSION, ALLOWED_DOCUMENT_EXTENSION
from internal.exception import FailException
from internal.model.upload_file import UploadFile
from internal.service.upload_file_service import UploadFileService


@inject
@dataclass
class CosService:
    """COS上传文件服务"""
    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, only_image: bool = False) -> UploadFile:
        """上传文件到腾讯云cos对象存储，上传后返回文件的信息"""

        # todo:等待授权认证模块完成进行切换调整
        account_id = '46db30d1-3199-4e79-a0cd-abf12fa6858f'

        # 检测文件扩展名是否满足要求
        filename = file.filename
        extension = file.filename.rsplit('.', 1)[-1] if "." in filename else ""
        if extension.lower() not in (ALLOWED_IMAGE_EXTENSION + ALLOWED_DOCUMENT_EXTENSION):
            raise FailException(f"不允许上传.{extension}扩展的文件")
        if only_image and extension not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"不允许上传.{extension}扩展的文件，请上传正确的图片")

        # 获取 COS 配置
        bucket = self._get_bucket()
        client = self._get_client()

        # 生成随机文件名
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 流式读取并上传COS
        file_content = file.stream.read()

        try:
            # 5.将数据上传到cos存储桶中
            client.put_object(bucket, file_content, upload_filename)
        except Exception as e:
            raise FailException("上传文件失败，请稍后重试")

        # 创建upload_file记录
        return self.upload_file_service.create_upload_file(
            account_id=account_id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        """下载cos云端的文件到指定路径"""
        client = self._get_client()
        bucket = self._get_bucket()

        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        """根据cos kye 获取图片URL"""
        cos_domain = os.getenv("COS_DOMAIN")
        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            scheme = os.getenv("COS_SCHEME")
            region = os.getenv("COS_REGION")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"

    @classmethod
    def _get_client(cls) -> CosS3Client:
        """获取腾讯云cos对象存储客户端"""
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https")
        )
        return CosS3Client(conf)

    @classmethod
    def _get_bucket(cls) -> str:
        """获取存储桶的名字"""
        return os.getenv("COS_BUCKET")
