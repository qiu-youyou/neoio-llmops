#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   sqlalchemay
@Time   :   2025/9/16 15:59
@Author :   s.qiu@foxmail.com
"""
from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


class SQLAlchemy(_SQLAlchemy):
    """基础SQLAlchemy类"""

    @contextmanager
    def auto_commit(self):
        """实现自动提交与回滚"""
        try:
            yield
            self.session.commit()
        except Exception as e:
            raise e
