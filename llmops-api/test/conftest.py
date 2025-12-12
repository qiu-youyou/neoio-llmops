#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   conftest
@Time   :   2025/9/12 11:31
@Author :   s.qiu@foxmail.com
"""
import pytest
from sqlalchemy.orm import sessionmaker, scoped_session

from app.http.app import app as _app
from internal.extension.database_extension import db as _db


@pytest.fixture()
def app():
    """获取并返回FLASK"""
    _app.config["TESTING"] = True
    return _app


@pytest.fixture()
def client(app):
    # 获取Flask测试端应用
    with app.test_client() as client:
        yield client


@pytest.fixture()
def db(app):
    """创建一个临时的数据库对话 测试结束后会滚事务 实现测试数据隔离"""
    with app.app_context():
        # 获取数据库连接创建事物
        connection = _db.engine.connect()
        transaction = connection.begin()

        # 创建临时会话
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session

        # 3.抛出数据库实例
        yield _db

        # 回退数据库并关闭连接 清除会话
        transaction.rollback()
        _db.session.close()
        session.remove()
