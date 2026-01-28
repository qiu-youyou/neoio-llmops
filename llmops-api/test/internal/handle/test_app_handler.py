#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_app_handle
@Time   :   2025/9/12 10:03
@Author :   s.qiu@foxmail.com
"""


class TestAppHandler:
    """App控制器测试类"""

    # @pytest.mark.parametrize("app_id, query", [
    #     ("0085001d-efa6-4022-86ae-60b9447c011f", None),
    #     ("0085001d-efa6-4022-86ae-60b9447c011f", "你好，你是?")
    # ])
    # def test_completion(self, app_id, query, client):
    #     pass
    # resp = client.post(f"/apps/{app_id}/debug", json={"query": query})
    # assert resp.status_code == 200
    # if query is None:
    #     assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
    # else:
    #     assert resp.json.get("code") == HttpCode.SUCCESS
