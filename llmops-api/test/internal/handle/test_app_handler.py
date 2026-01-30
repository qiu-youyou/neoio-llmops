#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_app_handle
@Time   :   2025/9/12 10:03
@Author :   s.qiu@foxmail.com
"""
import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """App控制器测试类"""

    @pytest.mark.parametrize("id", [
        "0085001d-efa6-4022-86ae-60b9447c011f",
        "0085001d-efa6-4022-86ae-60b9447c011d"
    ])
    def test_get_app(self, id, client):
        resp = client.get(f"/app/{id}")
        assert resp.status_code == 200
        if id.endswith("f"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif id.endswith("d"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_create_app(self, client):
        resp = client.post(f"/app")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("id", [
        "0085001d-efa6-4022-86ae-60b9447c011f",
    ])
    def test_update_app(self, id, client):
        resp = client.post(f"/app/{id}")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("id", [
        "0085001d-efa6-4022-86ae-60b9447c011f",
        "0085001d-efa6-4022-86ae-60b9447c011d"
    ])
    def test_delete_app(self, id, client):
        resp = client.post(f"/app{id}/delete")
        assert resp.status_code == 200
        if id.endswith("f"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif id.endswith("d"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("app_id, query", [
        ("0085001d-efa6-4022-86ae-60b9447c011f", None),
        ("0085001d-efa6-4022-86ae-60b9447c011f", "你好，你是?")
    ])
    def test_completion(self, app_id, query, client):
        resp = client.post(f"/apps/{app_id}/debug", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
