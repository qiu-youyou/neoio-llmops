#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   password
@Time   :   2026/1/28 16:18
@Author :   s.qiu@foxmail.com
"""
import base64
import hashlib
import re
from typing import Any

import binascii

# 密码校验，密码最少包含一个字母、一个数字，长度在8-16
password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,16}$"


def validate_password(password: str, pattern: str = password_pattern):
    """校验密码规则是否正确"""
    if re.match(pattern, password) is None:
        raise ValueError("密码格式错误，至少包含一个字母，一个数字，长度8-16位")
    return


def hash_password(password: str, salt: Any) -> bytes:
    """密码 哈希加密"""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return binascii.hexlify(dk)


def compare_password(password: str, password_hashed_base64: Any, salt_base64: Any) -> bool:
    """对比密码是否一致"""
    return hash_password(password, base64.b64decode(salt_base64)) == base64.b64decode(password_hashed_base64)
