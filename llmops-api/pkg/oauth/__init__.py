#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   __init__.py
@Time   :   2026/1/27 21:11
@Author :   s.qiu@foxmail.com
"""

from .github_oauth import GithubOAuth
from .oauth import OAuthUserInfo, OAuth

__all__ = ["OAuthUserInfo", "OAuth", "GithubOAuth"]
