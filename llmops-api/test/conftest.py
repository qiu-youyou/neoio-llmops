#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   conftest
@Time   :   2025/9/12 11:31
@Author :   s.qiu@foxmail.com
"""
import pytest

from app.http.app import app


@pytest.fixture()
def client():
    # 获取Flask测试端应用
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
