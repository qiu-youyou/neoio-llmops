#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   coversition_service
@Time   :   2026/1/21 10:52
@Author :   s.qiu@foxmail.com
"""
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from flask import Flask
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import SUMMARIZER_TEMPLATE, CONVERSATION_NAME_TEMPLATE, ConversationInfo, \
    SUGGESTED_QUESTIONS_TEMPLATE, SuggestedQuestions, InvokeFrom
from internal.model import Conversation, Message, MessageAgentThought
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ConversationService(BaseService):
    """会话服务"""
    db: SQLAlchemy

    def summary(self, human_message: str, ai_message: str, old_summary: str = "") -> str:
        """根据消息和旧的摘要生成 新摘要"""
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)
        llm = ChatOpenAI(model="kimi-k2-0905-preview", temperature=0.5)
        # 构建链应用
        chain = prompt | llm | StrOutputParser()
        new_summary = chain.invoke({
            "new_lines": f"Human: {human_message}\nAI: {ai_message}",
            "summary": old_summary,
        })

        return new_summary

    def generate_conversation_name(self, query: str) -> str:
        """根据 query 生成当前 会话名称"""

        # 提示词 注意：语言与用户的输入保持一致
        prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_NAME_TEMPLATE),
            ("human", "{query}")
        ])
        llm = ChatOpenAI(model="kimi-k2-0905-preview", temperature=0)
        structured_llm = llm.with_structured_output(ConversationInfo)
        chain = prompt | structured_llm

        # 提取query 截取过长的部分
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]" + query[-300:]
        query = query.replace("\n", " ")
        conversation_info = chain.invoke({"query": query})

        # 提取 会话名称
        name = "新的对话"
        try:
            if conversation_info and hasattr(conversation_info, "subject"):
                name = conversation_info.subject
        except Exception as e:
            logging.exception(f"提取会话名称错误，conversation_info:{conversation_info},错误信息：{str(e)}")

        if len(name) > 50:
            name = name[:50] + "..."

        return name

    def generate_suggested_questions(self, histories: str) -> list[str]:
        """根据历史信息生成 建议问题（不超过3条）"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", SUGGESTED_QUESTIONS_TEMPLATE),
            ("human", "{histories}")
        ])
        llm = ChatOpenAI(model="kimi-k2-0905-preview", temperature=0)
        structured_llm = llm.with_structured_output(SuggestedQuestions)
        chain = prompt | structured_llm
        suggested_questions = chain.invoke({"histories": histories})

        # 建议问题 提取
        questions = []
        try:
            if suggested_questions and hasattr(suggested_questions, "questions"):
                questions = suggested_questions.questions
        except Exception as e:
            logging.exception(f"生成建议问题错误，suggested_questions:{suggested_questions}, 错误信息:{str(e)}")

        if len(questions) > 3:
            questions = questions[:3]

        return questions

    def save_agent_thoughts(
            self, flask_app: Flask,
            account_id: UUID,
            app_id: UUID,
            app_config: dict[str, Any],
            conversation_id: UUID,
            message_id: UUID,
            agent_thoughts: list[AgentThought]):
        """存储智能体 推理消息"""
        with flask_app.app_context():
            position = 0
            latency = 0

            # 在子线程重新查询 保证会话有效性
            conversation = self.get(Conversation, conversation_id)
            message = self.get(Message, message_id)

            # 存储智能体推理过程
            for agent_thought in agent_thoughts:
                #  存储 记忆召回、推理、消息、动作、知识库检索 步骤
                if agent_thought.event in [
                    QueueEvent.AGENT_THOUGHT,
                    QueueEvent.AGENT_MESSAGE,
                    QueueEvent.AGENT_ACTION,
                    QueueEvent.DATASET_RETRIEVAL,
                ]:
                    # 更新位置及总耗时
                    position += 1
                    latency += agent_thought.latency
                    self.create(
                        MessageAgentThought,
                        app_id=app_id,
                        conversation_id=conversation.id,
                        message_id=message.id,
                        invoke_from=InvokeFrom.DEBUGGER,
                        created_by=account_id,
                        position=position,
                        event=agent_thought.event,
                        thought=agent_thought.thought,
                        observation=agent_thought.observation,
                        tool=agent_thought.tool,
                        tool_input=agent_thought.tool_input,
                        message=agent_thought.message,
                        answer=agent_thought.answer,
                        latency=agent_thought.latency,
                    )

                # 时间是否为 agent_message
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 更新消息
                    self.update(message, message=agent_thought.message, answer=agent_thought.answer,
                                latency=latency)

                    # 更新长期记忆
                    if app_config["long_term_memory"]["enable"]:
                        new_summary = self.summary(message.query, agent_thought.answer, conversation.summary)
                        self.update(conversation, summary=new_summary)

                    # 生成会话名称
                    if conversation.is_new:
                        new_conversation_name = self.generate_conversation_name(message.query)
                        self.update(conversation, name=new_conversation_name)

                    # 判断是否为停止或者错误，如果是则需要更新消息状态
                    if agent_thought.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT]:
                        self.update(
                            message,
                            status=agent_thought.event,
                            observation=agent_thought.observation
                        )
                        break
