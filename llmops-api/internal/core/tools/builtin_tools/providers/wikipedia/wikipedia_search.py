#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   wikipedia_search
@Time   :   2025/12/1 09:55
@Author :   s.qiu@foxmail.com
"""
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool


def wikipedia_search(**kwargs) -> BaseTool:
    """返回维基百科搜索工具"""
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper()
    )
