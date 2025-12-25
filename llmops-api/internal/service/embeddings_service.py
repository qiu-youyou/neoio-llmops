#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   embeddings_service
@Time   :   2025/12/23 10:35
@Author :   s.qiu@foxmail.com
"""
import os
# 过滤 import 相关的杂乱警告
import warnings
from dataclasses import dataclass

import tiktoken
from injector import inject
from langchain.embeddings import Embeddings
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis

warnings.filterwarnings("ignore", category=ImportWarning)


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings
    _base_cache_dir: str

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)
        # 初始化时设为 None，绝不加载模型
        self._embeddings = None
        self._cache_backed_embeddings = None

        # 预先计算好路径，但不读取
        self._base_cache_dir = os.path.join(os.getcwd(), "internal", "core", "embeddings")
        model_repo_id = "Alibaba-NLP/gte-multilingual-base"
        model_dir_name = f"models--{model_repo_id.replace('/', '--')}"
        snapshots_path = os.path.join(self._base_cache_dir, model_dir_name, "snapshots")

        # 寻找路径逻辑保持不变
        self._model_path = model_repo_id
        if os.path.exists(snapshots_path):
            subdirs = [d for d in os.listdir(snapshots_path) if os.path.isdir(os.path.join(snapshots_path, d))]
            if subdirs:
                self._model_path = os.path.join(snapshots_path, subdirs[0])

    def _load_model(self):
        """私有方法：真正执行加载模型（只运行一次）"""
        # if self._embeddings is None:
        if self._embeddings is not None:
            return

        print("⏳ [Embeddings] 正在首次加载模型到内存 (Lazy Loading)...")
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self._model_path,
            cache_folder=self._base_cache_dir,
            model_kwargs={
                "trust_remote_code": True,
                "local_files_only": True,
                "device": "cpu"
            }
        )

        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )
        print("✅ [Embeddings] 模型加载完成")

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.encoding_for_model("gpt-3.5")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        """获取 embeddings 时才触发加载"""
        if self._embeddings is None:
            self._load_model()
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        """获取 cached embeddings 时才触发加载"""
        if self._cache_backed_embeddings is None:
            self._load_model()
        return self._cache_backed_embeddings
