#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   base_agent
@Time   :   2026/1/23 09:00
@Author :   s.qiu@foxmail.com
"""

from abc import ABC, abstractmethod
from typing import Generator

from langchain_core.messages import AnyMessage

from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities import AgentConfig
from internal.core.agent.entities.queue_entity import AgentQueueEvent


class BaseAgent(ABC):
    """项目基础 AGENT"""

    def __init__(self, agent_config: AgentConfig, agent_queue_manager: AgentQueueManager):
        self.agent_config = agent_config
        self.agent_queue_manager = agent_queue_manager

    @abstractmethod
    def run(
            self,
            query: str,  # 原始问题
            history: list[AnyMessage] = None,  # 短期记忆
            long_term_memory: str = "",  # 长期记忆
    ) -> Generator[AgentQueueEvent, None, None]:
        """运行函数 接受提问、短期记忆、长期记忆"""
        raise NotImplementedError("AGENT Run 函数未实现")
