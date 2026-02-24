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

from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class AgentQueueManager:
    """智能体 队列管理器"""
    user_id: uuid.UUID
    invoke_from: InvokeFrom
    redis_client: Redis
    _queues: dict[str, Queue]

    def __init__(self, user_id: uuid.UUID, invoke_from: InvokeFrom):
        """初始化智能体队列管理器"""
        self.user_id = user_id
        self.invoke_from = invoke_from
        self._queues = {}

        # 内部初始化 redis_client
        from app.http.module import injector
        self.redis_client = injector.get(Redis)

    def publish(self, task_id: uuid.UUID, agent_thought: AgentThought) -> None:
        """发布事件到队列"""
        self.queue(task_id).put(agent_thought)

        # 判断是否为需要停止监听的事件类型
        if agent_thought.event in [QueueEvent.STOP, QueueEvent.ERROR, QueueEvent.TIMEOUT, QueueEvent.AGENT_END]:
            self.stop_listen(task_id)

    def publish_error(self, task_id: uuid.UUID, error) -> None:
        self.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation=str(error)
        ))

    def _is_stopped(self, task_id: uuid.UUID) -> bool:
        """监听是否停止"""
        task_stopped_cache_key = self.generate_task_stopped_cache_key(task_id)
        result = self.redis_client.get(task_stopped_cache_key)

        if result is not None:
            return True
        return False

    def stop_listen(self, task_id: uuid.UUID) -> None:
        """停止监听队列"""
        self.queue(task_id).put(None)

    def queue(self, task_id: uuid.UUID) -> Queue:
        """获取对应的任务队列信息"""
        q = self._queues.get(str(task_id))
        # 如果队列中不存在 创建队列并添加缓存键
        if not q:
            # 根据类型生成缓存键
            user_prefix = "account" if self.invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER] else "end-user"
            # 设置缓存 代表任务已经开始
            self.redis_client.setex(self.generate_task_belong_cache_key(task_id), 1800,
                                    f"{user_prefix}-{str(self.user_id)}")
            q = Queue()
            self._queues[str(task_id)] = q
        return q

    def listen(self, task_id: uuid.UUID) -> Generator:
        """监听队列"""
        # 记录超时时间、开始时间、最后一次PING通时间
        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        # 监听队列是否存在
        while True:
            try:
                item = self.queue(task_id).get(timeout=1)
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
                    self.publish(task_id, AgentThought(id=uuid.uuid4(), task_id=task_id, event=QueueEvent.PING))
                    last_ping_time = elapsed_time // 10

                # 是否超时 添加超时事件
                if elapsed_time >= listen_timeout:
                    self.publish(task_id, AgentThought(id=uuid.uuid4(), task_id=task_id, event=QueueEvent.TIMEOUT))

                # 是否停止 添加停止时间
                if self._is_stopped(task_id):
                    self.publish(task_id, AgentThought(id=uuid.uuid4(), task_id=task_id, event=QueueEvent.STOP))

    @classmethod
    def set_stop_flag(cls, task_id: uuid.UUID, invoke_from: InvokeFrom, user_id: uuid.UUID) -> None:
        """根据任务ID+调用来源停止会话"""
        # 获取 redis_client
        from app.http.module import injector
        redis_client = injector.get(Redis)
        # 获取当前正在执行的任务键
        result = redis_client.get(cls.generate_task_belong_cache_key(task_id))
        if not result:
            return

        # 计算对应缓存结果
        user_prefix = "account" if invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER] else "end-user"
        if result.decode("utf-8") != f"{user_prefix}-{str(user_id)}":
            return

        # 生成停止键标识
        stopped_cache_key = cls.generate_task_stopped_cache_key(task_id)
        redis_client.setex(stopped_cache_key, 600, 1)

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: uuid.UUID) -> str:
        """生成任务专属的缓存键"""
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: uuid.UUID) -> str:
        """生成任务已停止的缓存键"""
        return f"generate_task_stopped:{str(task_id)}"
