#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_app_handle
@Time   :   2025/9/12 10:03
@Author :   s.qiu@foxmail.com
"""

import pytest

from pkg.response import HttpCode


class TestAppHandle:
    """App控制器测试类"""

    @pytest.mark.parametrize("query", [None, 'hello'])
    def test_test(self, client, query):
        """测试接口"""
        resp = client.post('/test', json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("query", [None, 'hello'])
    def test_completion(self, client, query):
        """测试对话接口"""
        resp = client.post("/app/completion", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
