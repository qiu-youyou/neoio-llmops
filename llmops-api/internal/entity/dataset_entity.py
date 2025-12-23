#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_entity
@Time   :   2025/12/18 13:56
@Author :   s.qiu@foxmail.com
"""
from enum import Enum

# 知识库 descirption 默认格式化文本
DEFAULT_DATASET_DESCRIPTION_FORMATTER = "当你需要回答管理《{name}》的时候可以引用该知识库。"


class ProcessType(str, Enum):
    """文档处理规则类型 枚举"""
    AUTOMATIC = "automatic"
    CUSTOM = "custom"


# 默认的处理规则
DEFAULT_PROCESS_RULE = {
    "mode": "custom",
    "rule": {
        "pre_process_rules": [
            {"id": "remove_extra_space", "enabled": True},
            {"id": "remove_url_and_email", "enabled": True},
        ],
        "segment": {
            "separators": [
                "\n\n",
                "\n",
                "。|！|？",
                "\.\s|\!\s|\?\s",  # 英文标点符号后面通常需要加空格
                "；|;\s",
                "，|,\s",
                " ",
                ""
            ],
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
    }
}
