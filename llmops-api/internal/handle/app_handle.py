#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""

from internal.schema import CompletionReq
from pkg.response import validate_error_json


class AppHandle:
    """应用控制器"""

    def completion(self):
        # 校验接口
        req = CompletionReq()

        if not req.validate():
            return validate_error_json(req.errors)

        return "completion success"

    def test(self):
        return "testtest"
