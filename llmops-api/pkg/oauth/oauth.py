#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   oauth
@Time   :   2026/1/27 21:11
@Author :   s.qiu@foxmail.com
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """OAuth用户基础信息 记录 id/name/emails"""
    id: str
    name: str
    email: str


@dataclass
class OAuth(ABC):
    """第三方授权认证 基础类"""
    client_id: str  # 客户端id
    client_secret: str  # 客户端密钥
    redirect_uri: str  # 重定向uri

    @abstractmethod
    def get_provider(self) -> str:
        """获取服务提供者对应的名字"""
        pass

    @abstractmethod
    def get_authorization_url(self) -> str:
        """获取跳转授权认证的URL地址"""
        pass

    @abstractmethod
    def get_access_token(self, code: str) -> str:
        """根据传入的code获取授权令牌"""
        pass

    @abstractmethod
    def get_raw_user_info(self, token: str) -> dict:
        """根据传入的token获取OAuth原始信息"""
        pass

    @abstractmethod
    def transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        """将OAuth原始信息转换成OAuthUserInfo"""
        pass

    def get_user_info(self, token: str) -> OAuthUserInfo:
        """根据传入的token获取OAuthUserInfo信息"""
        raw_info = self.get_raw_user_info(token)
        return self.transform_user_info(raw_info)
