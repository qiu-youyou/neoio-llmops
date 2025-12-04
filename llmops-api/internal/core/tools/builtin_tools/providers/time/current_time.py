#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   current_time
@Time   :   2025/11/28 13:31
@Author :   s.qiu@foxmail.com
"""

from datetime import datetime
from typing import Any

from langchain.tools import BaseTool


class CurrentTimeTool(BaseTool):
    """用于获取当前时间的工具"""
    name: str = 'current_time'
    description: str = '一个用于获取当前时间的工具'

    def _run(self, *args, **kwargs) -> Any:
        """获取当前系统时间并格式化"""
        return datetime.now().strftime('%Y/%m/%d %H:%M:%S %Z')


def current_time(**kwargs) -> BaseTool:
    """返回获取当前时间的工具类"""
    return CurrentTimeTool()
