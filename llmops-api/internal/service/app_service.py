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

from internal.model import App, Account
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..exception import NotFoundException


@inject
@dataclass
class AppService(BaseService):
    """应用 服务"""
    db: SQLAlchemy

    def create_app(self, account: Account) -> App:
        with self.db.auto_commit():
            app = App()
            self.db.session.add(app)
        return app

    def get_app(self, id: uuid.UUID) -> App:
        app = self.db.session.query(App).get(id)
        if app is None:
            raise NotFoundException("应用不存在")
        return app

    def update_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = "Youyou"
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            if not app:
                raise NotFoundException("该应用不存在")
            self.db.session.delete(app)
        return app
