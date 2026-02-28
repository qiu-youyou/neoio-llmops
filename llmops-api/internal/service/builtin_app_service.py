#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   builtin_app_service
@Time   :   2026/2/28 22:02
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from injector import inject

from internal.core.builtin_apps import BuiltinAppManager
from internal.core.builtin_apps.entities.builtin_app_entity import BuiltinAppEntity
from internal.core.builtin_apps.entities.category_entity import CategoryEntity
from internal.model import Account, App, AppConfigVersion
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..entity.app_entity import AppStatus, AppConfigType


@inject
@dataclass
class BuiltinAppService(BaseService):
    """内置应用服务"""
    db: SQLAlchemy
    builtin_app_manager: BuiltinAppManager

    def get_categories(self) -> list[CategoryEntity]:
        """获取内置应用分类列表"""
        return self.builtin_app_manager.get_categories()

    def get_builtin_apps(self) -> list[BuiltinAppEntity]:
        """获取内置应用模版列表"""
        return self.builtin_app_manager.get_builtin_apps()

    def add_builtin_app_to_space(self, builtin_app_id: str, account: Account) -> App:
        """内置应用模板添加到工作区 添加到个人空间下"""

        # 获取内置应用模板
        builtin_app = self.builtin_app_manager.get_builtin_app(builtin_app_id)
        # 创建APP添加到数据库
        with self.db.auto_commit():
            app = App(account_id=account.id, status=AppStatus.DRAFT,
                      **builtin_app.model_dump(include={"name", "icon", "description"}))
            self.db.session.add(app)
            self.db.session.flush()

            # 创建APP配置添加到数据库
            draft_app_config = AppConfigVersion(
                app_id=app.id, model_config=builtin_app.language_model_config,
                config_type=AppConfigType.DRAFT,
                **builtin_app.model_dump(include={
                    "dialog_round", "preset_prompt", "tools", "retrieval_config",
                    "long_term_memory",
                    "opening_statement", "opening_questions", "speech_to_text",
                    "text_to_speech",
                    "review_config", "suggested_after_answer",
                }))
            self.db.session.add(draft_app_config)
            self.db.session.flush()

            # 草稿配置关联到APP
            app.app_config_id = draft_app_config.id

            return app
