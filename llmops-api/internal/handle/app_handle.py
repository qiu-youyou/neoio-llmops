#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
import os

from flask import request
from openai import OpenAI

from internal.schema import CompletionReq, TestReq
from pkg.response import validate_error_json, success_json


class AppHandle:
    """应用控制器"""

    def completion(self):
        # 校验接口参数
        req = CompletionReq()

        if not req.validate():
            return validate_error_json(req.errors)

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
        print(request)
        req = TestReq()

        if not req.validate():
            return validate_error_json(req.errors)

        return success_json({"content": 'abc'})

        # raise ForbiddenException("无权限")
        return "test......"
