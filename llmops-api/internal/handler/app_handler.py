#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
import uuid
from dataclasses import dataclass
from operator import itemgetter
from typing import Dict, Any
from uuid import UUID

from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnablePassthrough, RunnableLambda
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI

from internal.schema.app_schema import CompletionReq
from internal.service import AppService, VectorDatabaseService
from internal.task.demo_task import demo_task
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class AppHandler:
    """应用控制器"""
    app_service: AppService
    vector_database_service: VectorDatabaseService

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
            return validate_error_json(req.errors)

        # 提示词与记忆
        system_prompt = "你是一个强大的聊天机器人，能根据对应的上下文和历史对话信息回复用户问题。\n\n<context>{context}</context>"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ])

        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

        # 创建 LLM
        llm = ChatOpenAI(model="kimi-k2-0905-preview")

        retriever = self.vector_database_service.get_retriever() | self.vector_database_service.combine_documents

        # 创建调用链
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | itemgetter("history"),
            context=itemgetter("query") | retriever,
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_context)

        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config={"configurable": {"memory": memory}})

        return success_json({"content": content})

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储对应的上下文信息到记忆实体中"""
        # 加载记忆
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加载记忆变量信息"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    def test(self):
        demo_task.delay(uuid.uuid4())
        return success_json({})
        # raise ForbiddenException("无权限")
