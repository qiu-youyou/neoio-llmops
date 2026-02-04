#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   agent_queue_manager
@Time   :   2026/1/25 21:22
@Author :   s.qiu@foxmail.com
"""
import queue
import time
import uuid
from queue import Queue
from typing import Generator

from redis import Redis

from internal.core.agent.entities.queue_entity import AgentQueueEvent, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    """智能体 队列管理器"""
    q: Queue
    user_id: uuid.UUID
    task_id: uuid.UUID
    invoke_from: InvokeFrom
    redis_client: Redis

    def __init__(self, user_id: uuid.UUID, task_id: uuid.UUID, invoke_from: InvokeFrom, redis_client: Redis):
        """初始化智能体队列管理器"""
        self.q = Queue()
        self.user_id = user_id
        self.task_id = task_id
        self.invoke_from = invoke_from
        self.redis_client = redis_client

        # 根据类型生成缓存键
        user_prefix = "account" if self.invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER] else "end-user"

        # 设置缓存 代表任务已经开始
        self.redis_client.setex(self.generate_task_belong_cache_key(task_id), 1800, f"{user_prefix}-{str(user_id)}")

    def publish(self, agent_queue_event: AgentQueueEvent) -> None:
        """发布事件到队列"""
        self.q.put(agent_queue_event)

        # 判断是否为需要停止监听的事件类型
        if agent_queue_event.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT, QueueEvent.AGENT_END]:
            self.stop_listen()

    def stop_listen(self) -> None:
        """停止监听队列"""
        self.q.put(None)

    def publish_error(self, error) -> None:
        self.publish(AgentQueueEvent(
            id=uuid.uuid4(),
            task_id=self.task_id,
            event=QueueEvent.ERROR,
            observation=str(error),
        ))

    def _is_stopped(self) -> bool:
        """监听是否停止"""
        task_stopped_cache_key = self.generate_task_stopped_cache_key(self.task_id)
        result = self.redis_client.get(task_stopped_cache_key)

        if result is not None:
            return True
        return False

    def listen(self) -> Generator:
        """监听队列"""

        # 记录超时时间、开始时间、最后一次PING通时间
        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        # 监听队列是否存在
        while True:
            try:
                item = self.q.get(timeout=1)
                if item is None:
                    break
                yield item
            except queue.Empty:
                continue
            finally:
                # 获取数据总耗时
                elapsed_time = time.time() - start_time

                # 每十秒发送一次PING事件 保持心跳
                if elapsed_time // 10 > last_ping_time:
                    self.publish(AgentQueueEvent(id=uuid.uuid4(), task_id=self.task_id, event=QueueEvent.PING))
                    last_ping_time = elapsed_time // 10

                # 是否超时 添加超时事件
                if elapsed_time >= listen_timeout:
                    self.publish(AgentQueueEvent(id=uuid.uuid4(), task_id=self.task_id, event=QueueEvent.TIMEOUT))

                # 是否停止 添加停止时间
                if self._is_stopped():
                    self.publish(AgentQueueEvent(id=uuid.uuid4(), task_id=self.task_id, event=QueueEvent.STOP))

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: uuid.UUID) -> str:
        """生成任务专属的缓存键"""
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: uuid.UUID) -> str:
        """生成任务已停止的缓存键"""
        return f"generate_task_stopped:{str(task_id)}"
