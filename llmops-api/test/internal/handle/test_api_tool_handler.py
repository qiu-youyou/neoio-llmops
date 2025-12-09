#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_api_tool_handler
@Time   :   2025/12/9 13:12
@Author :   s.qiu@foxmail.com
"""

import pytest

from pkg.response import HttpCode

test_schema_string = "{\"description\":\"这是一个查询对应英文单词字典的工具\",\"server\":\"https://dict.youdao.com\",\"paths\":{\"/suggest\":{\"get\":{\"description\":\"根据传递的单词查询其字典信息\",\"operationId\":\"YoudaoSuggest\",\"parameters\":[{\"name\":\"q\",\"in\":\"query\",\"description\":\"要检索查询的单词，例如love/computer\",\"required\":true,\"type\":\"str\"},{\"name\":\"doctype\",\"in\":\"query\",\"description\":\"返回的数据类型，支持json和xml两种格式，默认情况下json数据\",\"required\":false,\"type\":\"str\"}]}}}}"


class TestApiToolHandler:
    """自定义工具处理器测试类"""

    @pytest.mark.parametrize("openapi_schema", ["123", test_schema_string])
    def test_validate_openapi_schema(self, openapi_schema, client):
        resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": openapi_schema})
        assert resp.status_code == 200
        if openapi_schema == "123":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        elif openapi_schema == test_schema_string:
            assert resp.json.get("code") == HttpCode.SUCCESS
