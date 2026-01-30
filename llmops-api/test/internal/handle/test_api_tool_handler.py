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

    @pytest.mark.parametrize("query", [
        {},
        {"current_page": 2},
        {"search_word": "有道搜索"},
        {"search_word": "TEST工具包"},
    ])
    def test_get_api_tool_providers_with_page(self, query, client):
        resp = client.get("/api-tools", query_string=query)
        assert resp.status_code == 200
        if query.get("current_page") == 2:
            assert len(resp.json.get("data").get("list")) == 0
        elif query.get("search_word") == "有道搜索":
            assert len(resp.json.get("data").get("list")) == 1
        elif query.get("search_word") == "TEST工具包":
            assert len(resp.json.get("data").get("list")) == 0
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    def test_create_api_tool_provider(self, client, db):
        data = {
            "name": "查询工具包",
            "icon": "https://gaode.example.com",
            "openapi_schema": "{\"description\":\"查询ip所在地、天气预报、路线规划等高德工具包\",\"server\":\"https://gaode.example.com\",\"paths\":{\"/weather\":{\"get\":{\"description\":\"根据传递的城市名获取指定城市的天气预报，例如：广州\",\"operationId\":\"GetCurrentWeather\",\"parameters\":[{\"name\":\"location\",\"in\":\"query\",\"description\":\"需要查询天气预报的城市名\",\"required\":true,\"type\":\"str\"}]}},\"/ip\":{\"post\":{\"description\":\"根据传递的ip查询ip归属地\",\"operationId\":\"GetCurrentIp\",\"parameters\":[{\"name\":\"ip\",\"in\":\"request_body\",\"description\":\"需要查询所在地的标准ip地址，例如:201.52.14.23\",\"required\":true,\"type\":\"str\"}]}}}}",
            "headers": [{"key": "Authorization", "value": "Bearer access_token"}]
        }
        resp = client.post("/api-tools", json=data)
        assert resp.status_code == 200

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).filter_by(name="查询工具包").one_or_none()
        assert api_tool_provider is not None

    def test_update_api_tool_provider(self, client, db):
        provider_id = "a9bff90b-f75f-4386-9e8f-f92b6a9ad5bb"
        data = {
            "name": "test_update_api_tool_provider",
            "icon": "https://gaode.example.com",
            "openapi_schema": "{\"description\":\"查询ip所在地、天气预报、路线规划等高德工具包\",\"server\":\"https://gaode.example.com\",\"paths\":{\"/weather\":{\"get\":{\"description\":\"根据传递的城市名获取指定城市的天气预报，例如：广州\",\"operationId\":\"GetCurrentWeather\",\"parameters\":[{\"name\":\"location\",\"in\":\"query\",\"description\":\"需要查询天气预报的城市名\",\"required\":true,\"type\":\"str\"}]}},\"/ip\":{\"post\":{\"description\":\"根据传递的ip查询ip归属地\",\"operationId\":\"GetLocationForIp\",\"parameters\":[{\"name\":\"ip\",\"in\":\"request_body\",\"description\":\"需要查询所在地的标准ip地址，例如:201.52.14.23\",\"required\":true,\"type\":\"str\"}]}}}}",
            "headers": [{"key": "Authorization", "value": "Bearer access_token"}]
        }
        resp = client.post(f"/api-tools/{provider_id}", json=data)
        assert resp.status_code == 200

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider.name == data.get("name")

    @pytest.mark.parametrize("provider_id", [
        "a9bff90b-f75f-4386-9e8f-f92b6a9ad5bb",
        "a9bff90b-f75f-4386-9e8f-f92b6a9ad5bc"
    ])
    def test_get_api_tool_provider(self, provider_id, client):
        resp = client.get(f"/api-tools/{provider_id}")
        assert resp.status_code == 200
        if provider_id.endswith("b"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif provider_id.endswith("c"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    @pytest.mark.parametrize("provider_id, tool_name", [
        ("a9bff90b-f75f-4386-9e8f-f92b6a9ad5bb", "YoudaoSuggest"),
        ("a9bff90b-f75f-4386-9e8f-f92b6a9ad5bb", "YoudaoSuggestABC")
    ])
    def test_get_api_tool(self, provider_id, tool_name, client):
        resp = client.get(f"/api-tools/{provider_id}/tools/{tool_name}")
        assert resp.status_code == 200
        if tool_name == "YoudaoSuggest":
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif tool_name == "YoudaoSuggestABC":
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_delete_api_tool_provider(self, client, db):
        provider_id = "a9bff90b-f75f-4386-9e8f-f92b6a9ad5bb"
        resp = client.post(f"/api-tools/{provider_id}/delete")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS

        from internal.model import ApiToolProvider
        api_tool_provider = db.session.query(ApiToolProvider).get(provider_id)
        assert api_tool_provider is None

    @pytest.mark.parametrize("openapi_schema", ["123", test_schema_string])
    def test_validate_openapi_schema(self, openapi_schema, client):
        resp = client.post("/api-tools/validate-openapi-schema", json={"openapi_schema": openapi_schema})
        assert resp.status_code == 200
        if openapi_schema == "123":
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        elif openapi_schema == test_schema_string:
            assert resp.json.get("code") == HttpCode.SUCCESS
