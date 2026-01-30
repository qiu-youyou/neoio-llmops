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
        "2f0433a3-58ee-4c71-bff0-c96372fd3c55",
        "78d98117-09ca-4318-91ac-46b352873e73"
    ])
    def test_get_app(self, id, client, db):
        resp = client.get(f"/app/{id}")
        assert resp.status_code == 200
        if id.endswith("5"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif id.endswith("3"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_create_app(self, client, db):
        resp = client.post(f"/app")
        assert resp.status_code == 200

    @pytest.mark.parametrize("id", [
        "2f0433a3-58ee-4c71-bff0-c96372fd3c55",
    ])
    def test_update_app(self, id, client, db):
        resp = client.post(f"/app/{id}")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("id", [
        "2f0433a3-58ee-4c71-bff0-c96372fd3c55",
        "78d98117-09ca-4318-91ac-46b352873e73"
    ])
    def test_delete_app(self, id, client, db):
        resp = client.post(f"/app/{id}/delete")
        assert resp.status_code == 200
        if id.endswith("5"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif id.endswith("3"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND
