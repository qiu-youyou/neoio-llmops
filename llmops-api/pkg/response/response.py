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
    """基础响应"""
    return jsonify(data), 200


def success_json(data: Any = None):
    """成功响应"""
    return json(Response(code=HttpCode.SUCCESS, data=data))


def fail_json(data: Any = None):
    """失败响应"""
    return json(Response(code=HttpCode.FAIL, data=data))


def validate_error_json(errors: dict = None):
    """数据验证错误响应"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(code=HttpCode.VALIDATE_ERROR, message=msg, data=errors))


def message(code: HttpCode = None, msg: str = ''):
    """消息提示响应"""
    return json(Response(code=code, message=msg, data={}))


def success_message(msg: str = ''):
    """成功消息响应"""
    return message(HttpCode.SUCCESS, msg)


def fail_message(msg: str = ''):
    """失败消息响应"""
    return message(HttpCode.FAIL, msg)


def not_found_message(msg: str = ""):
    """未找到消息响应"""
    return message(code=HttpCode.NOT_FOUND, msg=msg)


def unauthorized_message(msg: str = ""):
    """未授权消息响应"""
    return message(code=HttpCode.UNAUTHORIZED, msg=msg)


def forbidden_message(msg: str = ""):
    """无权限消息响应"""
    return message(code=HttpCode.FORBIDDEN, msg=msg)
