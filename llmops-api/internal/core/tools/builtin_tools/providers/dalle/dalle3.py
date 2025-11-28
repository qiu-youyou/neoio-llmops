#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dalle3
@Time   :   2025/11/28 15:14
@Author :   s.qiu@foxmail.com
"""
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class Dale3ArgsSchema(BaseModel):
    query: str = Field(description="输入应该是生成图像的文本提示(prompt)")


def dalle3(**kwargs) -> BaseTool:
    """返回DALLE3绘图工具"""

    return OpenAIDALLEImageGenerationTool(
        api_wrapper=DallEAPIWrapper(model='dall-e-2', **kwargs),
    )
