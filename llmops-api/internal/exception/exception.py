#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   exception
@Time   :   2025/9/11 11:25
@Author :   s.qiu@foxmail.com
"""
from typing import Any

from pkg.response import HttpCode


class CustomException(Exception):
    """自定义异常信息"""
    code: HttpCode = HttpCode.FAIL
    message: str = ""
    data: Any = None

    def __init__(self, message: str = '', data: Any = None) -> None:
        super().__init__()
        self.message = message
        self.data = data


class FailException(CustomException):
    """通用异常"""
    pass


class NotFoundException(CustomException):
    """未找到"""
    code = HttpCode.NOT_FOUND


class UnauthorizedException(CustomException):
    """未授权"""
    code = HttpCode.UNAUTHORIZED


class ForbiddenException(CustomException):
    """无权限"""
    code = HttpCode.FORBIDDEN


class ValidateErrorException(CustomException):
    """验证异常"""
    code = HttpCode.VALIDATE_ERROR
