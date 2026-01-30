#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   test_dataset_handler
@Time   :   2026/1/30 11:10
@Author :   s.qiu@foxmail.com
"""
import pytest

from internal.model import Dataset
from pkg.response import HttpCode


class TestDatasetHandler:
    """知识库处理器 测试类"""

    def test_create_dataset(self, client, db):
        data = {
            "name": "测试知识库PYTEST",
            "icon": "https://cdn.imooc.com/dataset.jpg",
            "description": "Useful for when you want to answer queries about the LLMOps知识库"
        }
        resp = client.post(f"/datasets", json=data)
        assert resp.status_code == 200
        dateset = db.session.query(Dataset).filter_by(name=data["name"]).one_or_none()
        assert dateset is not None

    @pytest.mark.parametrize("dataset_id", [
        "d9baab72-9e23-449a-8513-5acd9e235f33",
        "d9baab72-9e23-449a-8513-5acd9e235f34"
    ])
    def test_get_dataset(self, dataset_id, client, db):
        resp = client.get(f"/datasets/{dataset_id}")
        assert resp.status_code == 200
        if dataset_id.endswith("3"):
            assert resp.json.get("code") == HttpCode.SUCCESS
        elif dataset_id.endswith("4"):
            assert resp.json.get("code") == HttpCode.NOT_FOUND

    def test_update_dataset(self, client, db):
        data = {
            "name": "LLMOps测试知识库-01",
            "icon": "https://cdn.imooc.com/dataset.jpg",
            "description": "Useful for when you want to answer queries about the LLMOps知识库"
        }
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        resp = client.post(f"/datasets{dataset_id}", json=data)
        assert resp.status_code == 200
        dateset = db.session.query(Dataset).filter(Dataset.id == dataset_id).one_or_none()
        assert dateset is not None
        assert dateset.name == data["name"]

    @pytest.mark.parametrize("query", [
        {},
        {"current_page": 2},
        {"search_word": "测试"},
        {"search_word": "ABC"},
    ])
    def test_get_datasets_with_page(self, query, client, db):
        resp = client.get("/datasets", query_string=query)
        assert resp.status_code == 200
        if query.get("current_page") == 2:
            assert len(resp.json.get("data").get("list")) == 0
        elif query.get("search_word") == "测试":
            assert len(resp.json.get("data").get("list")) == 1
        elif query.get("search_word") == "ABC":
            assert len(resp.json.get("data").get("list")) == 0
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS

    # 涉及到向量数据库不进行测试
    # def test_delete_dataset(self, client, db):
    #     dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
    #     resp = client.post(f"/datasets/{dataset_id}/delete")
    #     assert resp.status_code == 200
    #     assert resp.json.get("code") == HttpCode.SUCCESS
    #
    #     from internal.model import Dataset
    #     dataset = db.session.query(Dataset).get(dataset_id)
    #     assert dataset is None

    def test_get_dataset_queries(self, client, db):
        dataset_id = "d9baab72-9e23-449a-8513-5acd9e235f33"
        resp = client.get(f"/datasets{dataset_id}/queries")
        assert resp.status_code == 200
        assert len(resp.json.get("data")) <= 10
