#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_segment_handler
@Time   :   2026/1/30 16:19
@Author :   s.qiu@foxmail.com
"""
import pytest

from pkg.response import HttpCode


class TestSegmentHandler:
    """文档片段处理器 测试类"""

    @pytest.mark.parametrize("query", [
        {},
        {"current_page": 2},
        {"search_word": "角色"},
        {"search_word": "ABC"},
    ])
    def test_get_segments_with_page(self, query, client, db):
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        document_id = "c632a35c-1638-400b-982e-db960e14b430"
        resp = client.get(f"/datasets/{dataset_id}/documents/{document_id}/segments", query_string=query)
        assert resp.status_code == 200
        if query.get("current_page") == 2:
            assert len(resp.json.get("data").get("list")) == 0
        elif query.get("search_word") == "角色":
            assert len(resp.json.get("data").get("list")) == 1
        elif query.get("search_word") == "ABC":
            assert len(resp.json.get("data").get("list")) == 0
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("dataset_id, document_id, segment_id", [
        ("d9baab72-9e23-449a-8513-5acd9e235f33", "c632a35c-1638-400b-982e-db960e14b430",
         "45e1743b-c450-49d5-93a5-cc39b7520bd5"),
        ("d9baab72-9e23-449a-8513-5acd9e235f33", "c632a35c-1638-400b-982e-db960e14b431",
         "45e1743b-c450-49d5-93a5-cc39b7520bd5"),
    ])
    def test_get_segment(self, dataset_id, document_id, segment_id, client, db):
        resp = client.get(f"/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}")
        assert resp.status_code == 200
        if document_id.endswith("0"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif document_id.endswith("1"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND
