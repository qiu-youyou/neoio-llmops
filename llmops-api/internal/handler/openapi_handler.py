#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   openapi_handler
@Time   :   2026/2/25 16:51
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.openapi_schema import OpenAPIChatReq
from internal.service import OpenApiService
from pkg.response import validate_error_json, compact_generate_response


@inject
@dataclass
class OpenApiHandler:
    """开放API控制器"""
    openapi_service: OpenApiService

    @login_required
    def chat(self):
        """开放API Chat对话接口"""

        req = OpenAPIChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        resp = self.openapi_service.chat(req, current_user)
        return compact_generate_response(resp)
