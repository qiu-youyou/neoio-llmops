#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   jieba_service
@Time   :   2025/12/22 12:04
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

import jieba
from injector import inject
from jieba.analyse import default_tfidf

from internal.entity.jieba_entity import STOPWORD_SET


@inject
@dataclass
class JiebaService:
    """jieba 分词服务"""

    def __init__(self):
        """扩展jieba停用词"""
        default_tfidf.stop_words = STOPWORD_SET

    @classmethod
    def extract_keywords(cls, text: str, max_keyword_pre_chunk: int = 10) -> list[str]:
        """根据输入的文本，提取对应文本的关键词列表"""
        return jieba.analyse.extract_tags(
            sentence=text,
            topK=max_keyword_pre_chunk,
        )
