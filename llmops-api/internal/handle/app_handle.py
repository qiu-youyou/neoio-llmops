#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
import os
import uuid
from dataclasses import dataclass

from injector import inject
from openai import OpenAI

from internal.schema import CompletionReq, TestReq
from internal.service.app_service import AppService
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class AppHandle:
    """应用控制器"""
    app_service: AppService

    def get_app(self, id: uuid.UUID):
        """查询APP记录"""
        app = self.app_service.get_app(id)
        return success_message(f"查询成功，name 为 {app.name}")

    def create_app(self):
        """创建APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功, id 为 {app.id}")

    def update_app(self, id: uuid.UUID):
        """更新APP记录"""
        app = self.app_service.update_app(id)
        return success_message(f"应用更新成功，修改后 name 为 {app.name}")

    def delete_app(self, id: uuid.UUID):
        """删除APP记录"""
        app = self.app_service.delete_app(id)
        return success_message(f"应用删除成功, id 为 {app.id}", )

    def completion(self):
        # 校验接口参数
        req = CompletionReq()

        if not req.validate():
            return validate_error_json(req.erros)

        # 构建OPENAI 发送请求
        client = OpenAI(base_url=os.getenv("OPENAI_API_BASE"))

        completion = client.chat.completions.create(
            model="kimi-k2-0905-preview",
            messages=[
                {"role": "system", "content": "你是OpenAI开发的聊天机器人，请根据用户的输入回复对应的信息"},
                {"role": "user", "content": req.query.data},
            ],
            temperature=0.6,
        )

        # 返回响应
        content = completion.choices[0].message.content

        return success_json({"content": content})

    def test(self):
        # 测试用测试用
        req = TestReq()

        if not req.validate():
            return validate_error_json(req.errors)

        return success_json({"content": 'abc'})
        # raise ForbiddenException("无权限")
