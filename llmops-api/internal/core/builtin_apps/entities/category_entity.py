#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   category_entity
@Time   :   2026/2/28 16:04
@Author :   s.qiu@foxmail.com
"""

from pydantic import BaseModel, Field


class CategoryEntity(BaseModel):
    """内置应用分类实体"""
    category: str = Field(default="")  # 唯一标识
    name: str = Field(default="")  # 分类名称
