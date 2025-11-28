#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.core.tools.builtin_tools.providers import ProviderFactory
from internal.schema import CompletionReq
from internal.service.app_service import AppService
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class AppHandle:
    """应用控制器"""
    app_service: AppService
    provider_factory: ProviderFactory

    def get_app(self, id: UUID):
        """查询APP记录"""
        app = self.app_service.get_app(id)
        return success_message(f"查询成功，name 为 {app.name}")

    def create_app(self):
        """创建APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功, id 为 {app.id}")

    def update_app(self, id: UUID):
        """更新APP记录"""
        app = self.app_service.update_app(id)
        return success_message(f"应用更新成功，修改后 name 为 {app.name}")

    def delete_app(self, id: UUID):
        """删除APP记录"""
        app = self.app_service.delete_app(id)
        return success_message(f"应用删除成功, id 为 {app.id}", )

    def debug(self, app_id: UUID):
        # 校验接口参数
        req = CompletionReq()

        if not req.validate():
            return validate_error_json(req.erros)

        prompt = ChatPromptTemplate.from_template('{query}')
        llm = ChatOpenAI(model='kimi-k2-0905-preview')

        chain = prompt | llm | StrOutputParser()

        content = chain.invoke(req.query.data)
        return success_json({"content": content})

    def test(self):
        # 测试用测试用
        google_serper = self.provider_factory.get_providers()
        print(google_serper)
        # print(google_serper.invoke('苹果公司是那一年成立的 创始人是谁'))
        # req = TestReq()
        #
        # if not req.validate():
        #     return validate_error_json(req.errors)

        return success_json({"content": 'abc'})
        # raise ForbiddenException("无权限")
