#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   embeddings_service.py
@Author :   s.qiu@foxmail.com
"""
import os
import threading
from pathlib import Path
from typing import Optional

import tiktoken
import torch
from injector import inject, singleton
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis

# 全局加载一次 encoding，避免每次调用函数都重新加载模型配置
_TIKTOKEN_ENCODING = tiktoken.encoding_for_model("gpt-3.5-turbo")


@inject
@singleton
class EmbeddingsService:
    """文本嵌入模型服务"""

    def __init__(self, redis: Redis):
        """构造函数，初始化存储器，准备懒加载"""
        self._store = RedisStore(client=redis)
        self._embeddings: Optional[Embeddings] = None
        self._cache_backed_embeddings: Optional[CacheBackedEmbeddings] = None

        # 线程锁，防止并发请求导致模型重复加载
        self._lock = threading.Lock()

        # 路径配置
        self._base_cache_dir = Path(os.getcwd()) / "internal" / "core" / "embeddings"
        self._model_repo_id = "Alibaba-NLP/gte-multilingual-base"
        self._model_path = self._resolve_model_path()

    def _resolve_model_path(self) -> str:
        """解析本地模型路径，如果存在 snapshot 则使用具体路径"""
        model_dir_name = f"models--{self._model_repo_id.replace('/', '--')}"
        snapshots_path = self._base_cache_dir / model_dir_name / "snapshots"

        if snapshots_path.exists():
            # 获取第一个子目录
            subdirs = [d for d in snapshots_path.iterdir() if d.is_dir()]
            if subdirs:
                return str(subdirs[0])
        return self._model_repo_id

    def _get_device(self) -> str:
        """自动选择最佳计算设备"""
        if torch.backends.mps.is_available():
            return "mps"  # macOS Apple Silicon
        elif torch.cuda.is_available():
            return "cuda"  # NVIDIA GPU
        return "cpu"

    def _load_model(self):
        """
        加载模型到内存 (Lazy Loading)
        使用双重检查锁定 (Double-Checked Locking) 确保线程安全
        """
        if self._embeddings is not None:
            return

        # 核心判断：如果是在 Flask 调试模式下，且不是真正的工作进程，则不加载模型
        if os.environ.get("FLASK_DEBUG") == "1" and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            # 此时是主监控进程，打印一行提示并直接返回
            # print("ℹ️ [Embeddings] 监控进程跳过模型加载...")
            return

        with self._lock:
            # 再次检查，防止在等待锁的过程中已被其他线程加载
            if self._embeddings is not None:
                return
            # --- 解决 "Some weights..." 提示的关键代码 ---
            from transformers import logging as tf_logging
            tf_logging.set_verbosity_error()
            
            print(f"⏳ [Embeddings] 正在首次加载模型 (Device: {self._get_device()})...")

            try:
                # 基础模型
                base_embeddings = HuggingFaceEmbeddings(
                    model_name=self._model_path,
                    cache_folder=str(self._base_cache_dir),
                    model_kwargs={
                        "trust_remote_code": True,
                        "local_files_only": True,
                        "device": self._get_device()
                    }
                )

                # 缓存层封装
                self._embeddings = base_embeddings  # 保留原始引用
                self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
                    base_embeddings,
                    self._store,
                    namespace="embeddings",
                )
                print("✅ [Embeddings] 模型加载完成")
            except Exception as e:
                print(f"❌ [Embeddings] 模型加载失败: {e}")
                raise e

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数 (高性能版)"""
        # encode 是纯 CPU 计算，非常快，但 encoding 对象的加载很慢
        return len(_TIKTOKEN_ENCODING.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        """获取原始 embeddings，自动触发加载"""
        if self._embeddings is None:
            self._load_model()
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        """获取带缓存的 embeddings，自动触发加载"""
        if self._cache_backed_embeddings is None:
            self._load_model()
        return self._cache_backed_embeddings
