#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_account_handler
@Time   :   2026/1/29 15:26
@Author :   s.qiu@foxmail.com
"""
import pytest

from pkg.response import HttpCode


class TestAccountHandler:
    """账号管理处理器 测试类"""

    def test_get_current_user(self, client):
        resp = client.get(f"/account")
        assert resp.status_code == 200

    @pytest.mark.parametrize("name", [
        "ZhangSan",
    ])
    def test_update_name(self, name, client, db):
        resp = client.post(f"/account/name", json={"name": name})
        assert resp.status_code == 200
        from internal.model import Account
        account = db.session.query(Account).filter(Account.name == name).one_or_none()
        assert account is not None
        assert account.name == name

    @pytest.mark.parametrize("avatar", [
        "test",
        "https://neoio-llmops-file-1331234758.cos.ap-guangzhou.myqcloud.com/2026/01/29/168ec57d-dba3-4763-94a2-012332039d31.png"
    ])
    def test_update_avatar(self, avatar, client, db):
        resp = client.post(f"/account/avatar", json={"avatar": avatar})
        assert resp.status_code == 200
        if avatar == "test":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("password", [
        "123456",
        "abcd1234"
    ])
    def test_update_password(self, password, client, db):
        resp = client.post(f"/account/password", json={"password": password})
        assert resp.status_code == 200
        if password == "123456":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        elif password == "abcd1234":
            assert resp.json.get("code") == HttpCode.SUCCESS
