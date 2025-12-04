#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   wikipedia_search
@Time   :   2025/12/1 09:55
@Author :   s.qiu@foxmail.com
"""
from langchain.tools import BaseTool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun, WikipediaQueryInput
from langchain_community.utilities import WikipediaAPIWrapper

from internal.lib.helper import add_attribute


@add_attribute('args_schema', WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """返回维基百科搜索工具"""
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper()
    )
