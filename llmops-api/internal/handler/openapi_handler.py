#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   openapi_handler
@Time   :   2026/2/25 16:51
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from injector import inject


@inject
@dataclass
class OpenApiHandler:
    """开放API控制器"""

    def chat(self):
        """开放API Chat对话接口"""
