#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   process_rule_service
@Time   :   2025/12/24 15:26
@Author :   s.qiu@foxmail.com
"""
import re
from typing import Callable

from langchain_text_splitters import TextSplitter, RecursiveCharacterTextSplitter

from internal.model import ProcessRule


class ProcessRuleService:
    """处理规则 服务"""

    @classmethod
    def get_text_splitter_by_process_rule(
            cls,
            process_rule: ProcessRule,
            length_function: Callable[[str], int] = len,
            **kwargs) -> TextSplitter:
        """根据处理规则 获取相应的文本分割器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=process_rule.rule["segment"]["chunk_size"],
            chunk_overlap=process_rule.rule["segment"]["chunk_overlap"],
            separators=process_rule.rule["segment"]["separators"],
            length_function=length_function,
            is_separator_regex=True,
            **kwargs
        )

    @classmethod
    def clean_text_by_process_rule(cls, text: str, process_rule: ProcessRule) -> str:
        """根据处理规则清除多余的字符串"""
        # 1.循环遍历所有与处理规则
        for pre_process_rule in process_rule.rule["pre_process_rules"]:
            # 2.删除多余空格
            if pre_process_rule["id"] == "remove_extra_space" and pre_process_rule["enabled"] is True:
                pattern = r'\n{3,}'
                text = re.sub(pattern, '\n\n', text)
                pattern = r'[\t\f\r\x20\u00a0\u1680\u180e\u2000-\u200a\u202f\u205f\u3000]{2,}'
                text = re.sub(pattern, ' ', text)
            # 3.删除多余的URL链接及邮箱
            if pre_process_rule["id"] == "remove_url_and_email" and pre_process_rule["enabled"] is True:
                pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
                text = re.sub(pattern, '', text)
                pattern = r'https?://[^\s]+'
                text = re.sub(pattern, '', text)

        return text
