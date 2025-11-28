#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   helper
@Time   :   2025/11/27 14:28
@Author :   s.qiu@foxmail.com
"""

import importlib
from typing import Any


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    """动态导入特定模块下的特定功能"""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)
