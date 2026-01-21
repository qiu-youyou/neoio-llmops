#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   coversition_service
@Time   :   2026/1/21 10:52
@Author :   s.qiu@foxmail.com
"""
import logging
from dataclasses import dataclass

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import SUMMARIZER_TEMPLATE, CONVERSATION_NAME_TEMPLATE, ConversationInfo, \
    SUGGESTED_QUESTIONS_TEMPLATE, SuggestedQuestions


@inject
@dataclass
class ConversationService():
    """会话服务"""

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
