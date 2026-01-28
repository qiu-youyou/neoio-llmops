#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   account_handler
@Time   :   2026/1/28 21:36
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass

from flask_login import login_required, current_user
from injector import inject

from internal.schema.account_schema import GetCurrentUserResp, UpdateNameReq, UpdateAvatarReq, UpdatePasswordReq
from internal.service import AccountService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class AccountHandler:
    """账号管理处理器"""
    account_service: AccountService

    @login_required
    def get_current_user(self):
        """获取当前用户信息"""
        resp = GetCurrentUserResp()
        return success_json(resp.dump(current_user))

    @login_required
    def update_name(self):
        """更新当前账户名称"""
        req = UpdateNameReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        self.account_service.update_account(current_user, name=req.name.data)
        return success_json("账户信息更新成功")

    @login_required
    def update_avatar(self):
        """更新当前用户头像"""
        req = UpdateAvatarReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        self.account_service.update_account(current_user, avatar=req.avatar.data)
        return success_json("账户信息更新成功")

    @login_required
    def update_password(self):
        """修改当前用户密码"""
        req = UpdatePasswordReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        self.account_service.update_password(current_user, req.password.data)
        return success_json("账户密码更新成功")
