#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   token_buffer_memory
@Time   :   2026/2/5 11:24
@Author :   s.qiu@foxmail.com
"""
from dataclasses import dataclass

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy


def simple_token_counter(messages: list) -> int:
    total = 0
    for m in messages:
        if hasattr(m, "content") and m.content:
            total += len(m.content) // 4  # 粗略估算 1 token ≈ 4 chars
    return total


@dataclass
class TokenBufferMemory:
    """基于token计数的缓冲记忆组件"""
    db: SQLAlchemy  # 数据库实例
    conversation: Conversation  # 会话模型
    model_instance: BaseLanguageModel  # LLM模型

    def get_history_prompt_messages(self, max_token_limit: int = 2000, message_limit: int = 10, ) -> list[AnyMessage]:
        """根据 token限制+消息数量 获取指定会话的历史消息列表"""
        if self.conversation is None:
            return []
        # 查询会话消息列表 过滤状态为正常的数据 倒叙排序
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status.in_([MessageStatus.NORMAL, MessageStatus.STOP])
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        # messages 转 langchain 消息
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([HumanMessage(message.query), AIMessage(message.answer)])

        # 剪切消息
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=simple_token_counter,
            strategy="last",
            start_on="human",
            end_on="ai",
        )

    def get_history_prompt_text(self, max_token_limit: int = 2000, message_limit: int = 10, human_prefix: str = "Human",
                                ai_prefix: str = "AI") -> str:
        """根据 token限制+消息数量 获取指定会话的历史消息文本 (短期记忆文本生成)"""
        messages = self.get_history_prompt_messages(max_token_limit=max_token_limit, message_limit=message_limit)
        # 将消息列表转位文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
