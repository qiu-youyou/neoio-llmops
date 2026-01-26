#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   jwt_service
@Time   :   2026/1/26 21:34
@Author :   s.qiu@foxmail.com
"""

import os
from dataclasses import dataclass
from typing import Any

import jwt
from injector import inject

from internal.exception import UnauthorizedException


@inject
@dataclass
class JWTService:
    """ JWT 服务"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        """根据 payload 生成 token """
        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        """根据 token 解析 payload"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("授权凭证已过期，请重新登录")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("token解析错误，请重新登录")
        except Exception as e:
            raise UnauthorizedException(str(e))
