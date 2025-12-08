#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_category_manager
@Time   :   2025/12/3 15:01
@Author :   s.qiu@foxmail.com
"""

import os
from typing import Any

import yaml
from injector import singleton
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


@singleton
class BuiltinCategoryManager(BaseModel):
    """内置的工具分类管理器"""
    category_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        """获取分类映射信息"""
        return self.category_map

    def _init_categories(self):
        """初始化分类数据"""
        # 检测数据是否已经处理
        if self.category_map:
            return

        # 获取yaml数据路径并加载
        current_path = os.path.abspath(__file__)
        categories_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(categories_path, "categories.yaml")

        with open(categories_yaml_path, encoding="utf-8") as f:
            categories_data = yaml.safe_load(f)

            # 循环遍历所有分类，并且将分类加载成实体信息
            for category in categories_data:
                category_entity = CategoryEntity(**category)

                # 读取分类图标数据
                icon_path = os.path.join(categories_path, "icons", category_entity.icon)
                if not os.path.exists(icon_path):
                    raise NotFoundException(f"缺少该分类{category_entity.category}的图标")

                # 读取icon数据
                with open(icon_path, encoding="utf-8") as f:
                    icon = f.read()

                self.category_map[category_entity.category] = {
                    "entity": category_entity,
                    "icon": icon,
                }
