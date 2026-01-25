#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   agent_queue_manager
@Time   :   2026/1/25 21:22
@Author :   s.qiu@foxmail.com
"""

from enum import Enum
from queue import Queue
from uuid import UUID

from redis import Redis

from internal.entity.conversation_entity import InvokeFrom


class PublishFrom(str, Enum):
    """发布来源，用于记录队列管理器中的发布来源"""
    APPLICATION_MANAGER = 1
    TASK_PIPELINE = 2


class AgentQueueManager:
    """智能体 队列管理器"""
    q: Queue
    user_id: UUID
    task_id: UUID
    invoke_from: InvokeFrom
    redis_client: Redis
