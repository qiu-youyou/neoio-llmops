#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   module
@Time   :   2025/9/17 11:51
@Author :   s.qiu@foxmail.com
"""

from flask_migrate import Migrate
from injector import Module, Binder

from internal.extension.database_extension import db
from internal.extension.migrate_extension import migrate
from pkg.sqlalchemy import SQLAlchemy


class ExtensionModule(Module):
    """扩展的依赖注入"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
