#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   embeddings_service
@Time   :   2025/12/18 16:46
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from injector import inject


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
