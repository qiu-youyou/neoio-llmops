#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   openapi_service
@Time   :   2026/2/27 13:44
@Author :   s.qiu@foxmail.com
"""

import json
from dataclasses import dataclass
from threading import Thread
from typing import Generator

from flask import current_app
from injector import inject
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from internal.core.agent.agents import FunctionCallAgent
from internal.core.agent.entities import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.memory import TokenBufferMemory
from internal.entity.app_entity import AppStatus
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account, EndUser, Conversation, Message
from internal.schema.openapi_schema import OpenAPIChatReq
from pkg.response import Response
from pkg.sqlalchemy import SQLAlchemy
from .app_config_service import AppConfigService
from .app_service import AppService
from .base_service import BaseService
from .conversation_service import ConversationService
from .retrieval_service import RetrievalService


@inject
@dataclass
class OpenApiService(BaseService):
    """开放API服务"""
    db: SQLAlchemy
    app_service: AppService
    app_config_service: AppConfigService
    retrieval_service: RetrievalService
    conversation_service: ConversationService

    def chat(self, req: OpenAPIChatReq, account: Account):
        """开放API 发起对话，返回块内容或生成器"""

        # 获取当前应用 应用状态是否已发布
        app = self.app_service.get_app(req.app_id.data, account)
        if app.status != AppStatus.PUBLISHED:
            raise NotFoundException("应用不存在或未发布！")

        # 是否传递了终端用户ID 如果传递了判断是否关联当前应用 否则需要创建终端用户
        if req.end_user_id.data:
            end_user = self.get(EndUser, req.end_user_id.data)
            if not end_user or end_user.app_id != app.id:
                raise ForbiddenException("当前账号不存在或未关联当前应用！")
        else:
            end_user = self.create(EndUser, **{"tenant_id": account.id, "app_id": app.id})

        # 是否传递了会话ID 传递了需要检测会话归属信息 否则需要创建会话
        if req.conversation_id.data:
            conversation = self.get(Conversation, req.conversation_id.data)
            if (
                    not conversation
                    or conversation.app_id != app.id
                    or conversation.invoke_from != InvokeFrom.SERVICE_API
                    or conversation.created_by != end_user.id
            ):
                raise ForbiddenException("会话不存在或不属于该用户/应用/调用方式")
        else:
            conversation = self.create(Conversation, **{
                "app_id": app.id,
                "name": "New Conversation",
                "invoke_from": InvokeFrom.SERVICE_API,
                "created_by": end_user.id,
            })

        # 获取当前应用的运行配置
        app_config = self.app_config_service.get_app_config(app)

        # 根据用户查询创建消息记录
        message = self.create(Message, **{
            "app_id": app.id,
            "conversation_id": conversation.id,
            "invoke_from": InvokeFrom.SERVICE_API,
            "created_by": end_user.id,
            "query": req.query.data,
            "status": MessageStatus.NORMAL
        })

        # 创建 LLM todo:后续多LLM接入
        llm = ChatOpenAI(model=app_config["model_config"]["model"], **app_config["model_config"]["parameters"])

        # 提取短期记忆
        token_buffer_memory = TokenBufferMemory(db=self.db, conversation=conversation, model_instance=llm)
        history = token_buffer_memory.get_history_prompt_messages(message_limit=app_config["dialog_round"])

        # 该应用配置的工具转换为 langchain 工具
        tools = self.app_config_service.get_langchain_tools_by_tools_config(app_config["tools"])

        # 是否关联知识库 构建知识库检索 langchain 工具
        if app_config["datasets"]:
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=[dataset["id"] for dataset in app_config["datasets"]],
                account_id=account.id,
                retrival_source=RetrievalSource.APP,
                **app_config["retrieval_config"],
            )
            tools.append(dataset_retrieval)

        # 构建智能体
        agent = FunctionCallAgent(llm=llm, agent_config=AgentConfig(
            user_id=account.id,
            invoke_from=InvokeFrom.DEBUGGER,
            enable_long_term_memory=app_config["long_term_memory"]["enable"],
            tools=tools,
            review_config=app_config["review_config"],
        ))

        agent_state = {
            "messages": [HumanMessage(req.query.data)],
            "long_term_memory": conversation.summary,
            "history": history,
        }

        # 判断传递的 stream 流式响应/块响应
        if req.stream.data is True:
            # 处理流式响应
            agent_thoughts = {}

            def handle_stream(
                    end_user_id: str,
                    conversation_id: str,
                    message_id: str,
                    account_id: str,
                    app_id: str) -> Generator:
                """函数返回 yield 作为生成器"""

                for agent_thought in agent.stream(agent_state):
                    event_id = str(agent_thought.id)
                    # agent_thought 填充数据 除 agent_message 外的消息都进行覆盖处理
                    if agent_thought.event != QueueEvent.PING:
                        if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                            if event_id not in agent_thoughts:
                                agent_thoughts[event_id] = agent_thought
                            else:
                                agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                                    "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                                    "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                                    "latency": agent_thought.latency,
                                })
                        else:
                            agent_thoughts[event_id] = agent_thought
                    data = {
                        **agent_thought.model_dump(include={
                            "event", "thought", "observation", "tool", "tool_input", "answer", "latency",
                        }),
                        "id": event_id,
                        "end_user_id": end_user_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                        "task_id": str(agent_thought.task_id),
                    }
                    yield f"event: {agent_thought.event}\ndata: {json.dumps(data)}\n\n"

                # 将消息以及推理过程添加到数据库记录
                thread = Thread(target=self.conversation_service.save_agent_thoughts, kwargs={
                    "flask_app": current_app._get_current_object(),
                    "account_id": account_id,
                    "app_id": app_id,
                    "app_config": app_config,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "agent_thoughts": [agent_thought for agent_thought in agent_thoughts.values()],
                })
                thread.start()

            end_user_id = str(end_user.id)
            conversation_id = str(conversation.id)
            message_id = str(message.id)
            account_id = account.id
            app_id = app.id

            return handle_stream(end_user_id, conversation_id, message_id, account_id, app_id)

        # 块内容输出 并将消息和推理过程添加到数据库
        agent_result = agent.invoke(agent_state)
        thread = Thread(
            target=self.conversation_service.save_agent_thoughts,
            kwargs={
                "flask_app": current_app._get_current_object(),
                "account_id": account.id,
                "app_id": app.id,
                "app_config": app_config,
                "conversation_id": conversation.id,
                "message_id": message.id,
                "agent_thoughts": agent_result.agent_thoughts,
            }
        )
        thread.start()

        return Response(data={
            "id": str(message.id),
            "end_user_id": str(end_user.id),
            "conversation_id": str(conversation.id),
            "query": req.query.data,
            "answer": agent_result.answer,
            "total_token_count": 0,
            "latency": agent_result.latency,
            "agent_thoughts": [{
                "id": str(agent_thought.id),
                "event": agent_thought.event,
                "thought": agent_thought.thought,
                "observation": agent_thought.observation,
                "tool": agent_thought.tool,
                "tool_input": agent_thought.tool_input,
                "latency": agent_thought.latency,
                "created_at": 0,
            } for agent_thought in agent_result.agent_thoughts]
        })
