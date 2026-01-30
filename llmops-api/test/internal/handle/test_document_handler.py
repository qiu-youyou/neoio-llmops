#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_document_handler
@Time   :   2026/1/30 13:30
@Author :   s.qiu@foxmail.com
"""
import pytest

from internal.model import Document
from pkg.response import HttpCode


class TestDocumentHandle:
    """文档处理器 测试类"""

    @pytest.mark.parametrize("query", [
        {},
        {"current_page": 2},
        {"search_word": "TXT"},
        {"search_word": "ABC"},
    ])
    def test_get_documents_with_page(self, query, client, db):
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        resp = client.get(f"/datasets/{dataset_id}/documents", query_string=query)
        assert resp.status_code == 200
        if query.get("current_page") == 2:
            assert len(resp.json.get("data").get("list")) == 0
        elif query.get("search_word") == "TXT":
            assert len(resp.json.get("data").get("list")) == 1
        elif query.get("search_word") == "ABC":
            assert len(resp.json.get("data").get("list")) == 0
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    @pytest.mark.parametrize("dataset_id, document_id", [
        ("d9baab72-9e23-449a-8513-5acd9e235f33", "c632a35c-1638-400b-982e-db960e14b430"),
        ("d9baab72-9e23-449a-8513-5acd9e235f33", "c632a35c-1638-400b-982e-db960e14b431"),
    ])
    def test_get_document(self, dataset_id, document_id, client, db):
        resp = client.get(f"/datasets/{dataset_id}/documents/{document_id}")
        assert resp.status_code == 200
        if document_id.endswith("0"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif document_id.endswith("1"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_update_document_name(self, client, db):
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        document_id = "c632a35c-1638-400b-982e-db960e14b430"
        data = {"name": "测试修改文档名称"}
        resp = client.post(f"/datasets/{dataset_id}/documents/{document_id}/name", json=data)
        assert resp.status_code == 200
        document = db.session.query(Document).filter(Document.id == document_id).one_or_none()
        assert document is not None
        assert document.name == data["name"]

    def test_get_documents_status(self, client, db):
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        batch = "20260120093838928333"
        resp = client.get(f"/datasets/{dataset_id}/documents/batch/{batch}")
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
