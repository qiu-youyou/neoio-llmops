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
from .base_service import BaseService


@inject
@dataclass
class AppService(BaseService):
    """应用 服务"""
    db: SQLAlchemy

    def get_app(self, id: uuid.UUID) -> App:
        # 查询
        app = self.db.session.query(App).get(id)
        return app

    def create_app(self) -> App:
        # 创建
        app = self.create(App,
                          account_id=uuid.uuid4(),
                          name="测试机器人",
                          description="这是一个简单的聊天机器人",
                          icon="")
        return app

    def update_app(self, id: uuid.UUID) -> App:
        # 更新
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = "Youyou机器人"
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        # 删除
        with self.db.auto_commit():
            app = self.get_app(id)
            self.db.session.delete(app)
        return app
