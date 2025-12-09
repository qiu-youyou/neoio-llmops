#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   schema
@Time   :   2025/12/9 13:39
@Author :   s.qiu@foxmail.com
"""
from wtforms import Field


class ListField(Field):
    """自定义 list 字段"""
    data: list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data else []


class DictField(Field):
    """自定义 dict 字段"""
    data: dict = None

    def process_formdata(self, valuelist):
        if valuelist is not None and len(valuelist) and isinstance(valuelist[0], dict):
            self.data = valuelist[0]

    def _value(self):
        return self.data
