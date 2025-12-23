#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   embeddings_service
@Time   :   2025/12/23 10:35
@Author :   s.qiu@foxmail.com
"""
import os
from dataclasses import dataclass

import tiktoken
from injector import inject
from langchain.embeddings import Embeddings
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)

        # 1. 定义基础缓存路径
        base_cache_dir = os.path.join(os.getcwd(), "internal", "core", "embeddings")
        model_repo_id = "Alibaba-NLP/gte-multilingual-base"

        # 2. 构造模型在缓存中的目录名 (规则是 models--作者--模型名)
        model_dir_name = f"models--{model_repo_id.replace('/', '--')}"
        snapshots_path = os.path.join(base_cache_dir, model_dir_name, "snapshots")

        # 3. 寻找真实的模型路径
        final_model_path = model_repo_id  # 默认回退到 ID，防止找不到路径

        if os.path.exists(snapshots_path):
            # 获取 snapshots 下的所有子文件夹
            subdirs = [d for d in os.listdir(snapshots_path) if os.path.isdir(os.path.join(snapshots_path, d))]
            if subdirs:
                # 排序取最新的一个（通常只有一个哈希文件夹）
                # 比如: internal/core/embeddings/models--Alibaba.../snapshots/8fd7c4...
                final_model_path = os.path.join(snapshots_path, subdirs[0])
                print(f"✅ [Embeddings] 强制使用离线模型路径: {final_model_path}")
            else:
                print(f"⚠️ [Embeddings] 警告: 找到 snapshots 目录但为空: {snapshots_path}")
        else:
            print(f"⚠️ [Embeddings] 警告: 未找到本地缓存路径: {snapshots_path}，将尝试联网下载")

        # 4. 初始化 HuggingFaceEmbeddings
        self._embeddings = HuggingFaceEmbeddings(
            # 关键点：这里传入的是绝对路径，而不是 "Alibaba-NLP/..."
            model_name=final_model_path,

            # cache_folder 虽然此时不是必须的（因为路径已指定），但保留也没坏处
            cache_folder=base_cache_dir,

            model_kwargs={
                "trust_remote_code": True,
                # 当传入绝对路径时，local_files_only 实际上已经隐含了，但写上也无妨
                "local_files_only": True,
            }
        )

        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.encoding_name_for_model("gpt-3.5")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
