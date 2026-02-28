#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_app_manager
@Time   :   2026/2/28 15:22
@Author :   s.qiu@foxmail.com
"""
import os

import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field

from internal.core.builtin_apps.entities.builtin_app_entity import BuiltinAppEntity
from internal.core.builtin_apps.entities.category_entity import CategoryEntity


@inject
@singleton
class BuiltinAppManager(BaseModel):
    """内置应用管理器"""
    builtin_app_map: dict[str, BuiltinAppEntity] = Field(default_factory=dict)
    categories: list[CategoryEntity] = Field(default_factory=list)

    def __init__(self, **kwargs):
        """初始化内置应用分类以及内置应用列表"""
        super().__init__(**kwargs)
        self._init_categories()
        self._init_builtin_app_map()

    def get_categories(self) -> list[CategoryEntity]:
        """获取内置应用分类列表"""
        return self.categories

    def get_builtin_app(self, builtin_app_id: str) -> BuiltinAppEntity:
        """根据ID获取内置应用"""
        return self.builtin_app_map.get(builtin_app_id, None)

    def get_builtin_apps(self) -> list[BuiltinAppEntity]:
        """获取内置应用列表"""
        return [builtin_app for builtin_app in self.builtin_app_map.values()]

    def _init_categories(self):
        """初始化内置应用分类"""
        if self.categories:
            return
        # 读取分类 yaml 文件
        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(parent_path, "categories", "categories.yaml")

        with open(categories_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)
        self.categories = [CategoryEntity(**category) for category in categories]

    def _init_builtin_app_map(self):
        """初始化所有内置应用"""
        if self.builtin_app_map:
            return

        current_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(current_path)
        builtin_apps_yaml_path = os.path.join(parent_path, "builtin_apps")
        # 遍历读取文件夹中的所有 yaml 文件
        for filename in os.listdir(builtin_apps_yaml_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(builtin_apps_yaml_path, filename)
                with open(file_path, encoding="utf-8") as f:
                    builtin_app = yaml.safe_load(f)
                # 转换字段
                builtin_app["language_model_config"] = builtin_app.pop("model_config")
                self.builtin_app_map[builtin_app.get("id")] = BuiltinAppEntity(**builtin_app)
