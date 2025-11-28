#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   duckduckgo
@Time   :   2025/11/28 13:54
@Author :   s.qiu@foxmail.com
"""

from langchain_community.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field


class DDGInput(BaseModel):
    query: str = Field(description="需要索索的查询语句")


def duckduckgo_search(*args, **kwargs) -> BaseTool:
    """返回 DuckDuckGo 搜索工具"""
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，当你需要搜索时事时可以使用该工具，工具的输入是一个查询语句",
        args_schema=DDGInput
    )
