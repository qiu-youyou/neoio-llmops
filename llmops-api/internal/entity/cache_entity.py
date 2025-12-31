#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   cache_entity
@Time   :   2025/12/31 10:05
@Author :   s.qiu@foxmail.com
"""
# 缓存过期时间 默认 600 s
LOCK_EXPIRE_TIME = 600

# 知识库文档启用状态变更 缓存锁
LOCK_DOCUMENT_UPDATE_ENABLED = "lock:document:update:enabled_{document_id}"

# 关键词表的更新 缓存锁
LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE = "lock:keyword_table:update:keyword_table_{dataset_id}"

# 文档片段启用状态变更 缓存锁
LOCK_SEGMENT_UPDATE_ENABLED = "lock:segment:update:enabled_{segment_id}"
