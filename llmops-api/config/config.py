#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   config.py
@Time   :   2025/9/9 15:48
@Author :   s.qiu@foxmail.com
"""

import os
from typing import Any

from .default_config import DEFAULT_CONFIG


def _get_env(key: str) -> Any:
    """从环境变量中获取配置项 如果没有返回默认值"""
    return os.environ.get(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key: str) -> bool:
    """从环境变量中获取布尔配置项 找不到返回 False"""
    value: str = _get_env(key)
    return value.lower() == "true" if value is not None else False


class Config:
    def __init__(self):
        self.WTF_CSRF_ENABLED = _get_bool_env('WTF_CSRF_ENABLED')
