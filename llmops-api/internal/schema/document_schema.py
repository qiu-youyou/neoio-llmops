#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   document_schema
@Time   :   2025/12/22 20:57
@Author :   s.qiu@foxmail.com
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, AnyOf

from internal.entity.dataset_entity import ProcessType
from internal.model import Document
from internal.schema import ListField
from internal.schema.schema import DictField


class CreateDocumentReq(FlaskForm):
    """新增文档列表请求"""
    upload_file_ids = ListField("upload_file_ids")
    process_type = StringField("process_type", validators=[
        DataRequired("文档处理类型不能为空"),
        AnyOf(values=[ProcessType.AUTOMATIC, ProcessType.CUSTOM], message="处理类型格式错误")
    ])
    rule = DictField("rule")

    def validate_upload_file_ids(form, field: ListField) -> None:
        """校验文件id列表"""
        # todo:::
        # 校验数据类型与非空

        # 最长不能超过10条记录

        # 校验ID是否为UUID 通过 uuid.UUID 将字符串转换为UUID是否成功

        # 删除重复数据 转换为字典后再转换为list

    def validate_rule(form, field: DictField) -> None:
        """校验处理规则"""

        # 如果为自动 rule赋值为默认值

        # 自定有处理类型是否传递了 rule

        # 校验预处理规则，涵盖 非空、列表类型

        # 校验 enabled 参数

        # 过滤无关的数据

        # 判断是否传递了两个规则


class CreateDocumentResp(Schema):
    """新增文档列表响应"""
    documents = fields.List(fields.Dict, dump_only=[])
    batch = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: tuple[list[Document], str], **kwargs):
        return {
            "documents": [{
                "id": document.id,
                "name": document.name,
                "status": document.status,
                "create_at": int(document.create_at.timestamp()),
            } for document in data[0]],
            "batch": data[1],
        }
