#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   response
@Time   :   2025/9/10 14:13
@Author :   s.qiu@foxmail.com
"""
from dataclasses import field, dataclass
from typing import Any

from flask import jsonify

from .http_code import HttpCode


@dataclass
class Response:
    """基础HTTP接口响应格式"""
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)


def json(data: Response = None):
    return jsonify(data), 200


def validate_error_json(errors: dict = None):
    """数据验证错误响应"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(code=HttpCode.VALIDATE_ERROR, message=msg, data=errors))
