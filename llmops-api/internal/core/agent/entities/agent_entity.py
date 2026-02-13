#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   agent_entity
@Time   :   2026/1/23 09:03
@Author :   s.qiu@foxmail.com
"""
from uuid import UUID

from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from internal.entity.app_entity import DEFAULT_APP_CONFIG
from internal.entity.conversation_entity import InvokeFrom

# AGENT 预设提示词 模板
AGENT_SYSTEM_PROMPT_TEMPLATE = """你是一个高度定制的智能体应用，旨在为用户提供准确、专业的内容生成和问题解答，请严格遵守以下规则：

1.**预设任务执行**
  - 你需要基于用户提供的预设提示(PRESET-PROMPT)，按照要求生成特定内容，确保输出符合用户的预期和指引；

2.**工具调用和参数生成**
  - 当任务需要时，你可以调用绑定的外部工具(如知识库检索、计算工具等)，并生成符合任务需求的调用参数，确保工具使用的准确性和高效性；

3.**历史对话和长期记忆**
  - 你可以参考`历史对话`记录，结合经过摘要提取的`长期记忆`，以提供更加个性化和上下文相关的回复，这将有助于在连续对话中保持一致性，并提供更加精确的反馈；

4.**外部知识库检索**
  - 如果用户的问题超出当前的知识范围或需要额外补充，你可以调用`recall_dataset(知识库检索工具)`以获取外部信息，确保答案的完整性和正确性；

5.**高效性和简洁性**
  - 保持对用户需求的精准理解和高效响应，提供简洁且有效的答案，避免冗长或无关信息；

<预设提示>
{preset_prompt}
</预设提示>

<长期记忆>
{long_term_memory}
</长期记忆>
"""


class AgentConfig(BaseModel):
    """AGENT 配置： LLM模型、预设PROMPT、插件、知识库、工作流、是否开启长期记忆等等 随时扩展"""
    # 用户唯一标识
    user_id: UUID
    # 调用来源 默认：WEB_APP
    invoke_from: InvokeFrom = InvokeFrom.WEB_APP

    # 智能体预设提示词
    system_prompt: str = AGENT_SYSTEM_PROMPT_TEMPLATE
    # 预设prompt，默认为空，该值由前端用户在编排的时候记录，并填充到system_prompt中
    preset_prompt: str = ""

    # 智能体长期记忆是否开启
    enable_long_term_memory: bool = False  # 是否开启会话信息汇总/长期记忆

    # 智能体使用的工具列表
    tools: list[BaseTool] = Field(default_factory=list)

    # 审核配置
    review_config: dict = Field(default_factory=lambda: DEFAULT_APP_CONFIG["review_config"])


class AgentState(MessagesState):
    """智能体状态类"""
    task_id: UUID  # 该次状态对应的任务id，每次运行时会使用独立的任务id
    iteration_count: int  # 迭代次数，默认为0
    history: list[AnyMessage]  # 短期记忆(历史记录)
    long_term_memory: str  # 长期记忆


# 知识库检索工具名称
DATASET_RETRIEVAL_TOOL_NAME = "dataset_retrieval"

# Agent超过最大迭代次数时提示内容
MAX_ITERATION_RESPONSE = "当前Agent迭代次数已超过限制，请重试"
