#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_service
@Time   :   2025/9/17 16:21
@Author :   s.qiu@foxmail.com
"""

import uuid
from dataclasses import dataclass

from injector import inject

from internal.model import App
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AppService:
    """应用 服务"""
    db: SQLAlchemy

    def get_app(self, id: uuid.UUID) -> App:
        # 查询
        app = self.db.session.query(App).get(id)
        return app

    def create_app(self) -> App:
        # 创建
        with self.db.auto_commit():
            app = App(account_id=uuid.uuid4(), name="testName", description="test description", icon="")
            self.db.session.add(app)
        return app

    def update_app(self, id: uuid.UUID) -> App:
        # 更新
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = 'ZhangSan'
            self.db.session.add(app)
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        # 删除
        with self.db.auto_commit():
            app = self.get_app(id)
            self.db.session.delete(app)
        return app
