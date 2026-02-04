#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   function_call_agent
@Time   :   2026/1/23 10:05
@Author :   s.qiu@foxmail.com
"""

import json
import time
import uuid
from threading import Thread
from typing import Literal, Generator

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, RemoveMessage, ToolMessage, \
    messages_to_dict
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE
from internal.core.agent.entities.queue_entity import AgentQueueEvent, QueueEvent
from internal.exception import FailException
from .base_agent import BaseAgent


class FunctionCallAgent(BaseAgent):
    """工具函数调用智能体"""

    def run(
            self,
            query: str,
            history: list[AnyMessage] = None,
            long_term_memory: str = "") -> Generator[AgentQueueEvent, None, None]:
        """运行Agent应用"""
        if history is None:
            history = []

        agent = self._build_graph()

        thread = Thread(target=agent.invoke, args=({
            "messages": [HumanMessage(content=query)],
            "history": history,
            "long_term_memory": long_term_memory
        }))
        thread.start()

        yield from self.agent_queue_manager.listen()

    def _build_graph(self) -> CompiledStateGraph:
        """LANGGRAPH 图程序构建"""

        # 创建图 创建节点
        graph = StateGraph(AgentState)
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        # 起点、终点、条件变
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", 'llm')

        # 编译
        agent = graph.compile()
        return agent

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """长期记忆召回 节点"""

        # 获取配置 是否开启长期记忆
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]

            # 发布长记忆召回事件
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=uuid.uuid4(),
                task_id=self.agent_queue_manager.task_id,
                event=AgentQueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory
            ))

        # 构建系统预设消息 preset_prompt+long_term_memory
        preset_prompt = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory
            ))
        ]

        # 将 history 添加到消息列表
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            if len(history) % 2 != 0:
                raise FailException("历史消息列表格式错误")
            preset_prompt.extend(history)

        # 将 query 当前提问 进行拼接
        human_message = state["messages"][-1]
        preset_prompt.append(HumanMessage(content=human_message.content))

        return {"messages": [RemoveMessage(id=human_message.id), *preset_prompt]}

    def _llm_node(self, state: AgentState) -> AgentState:
        """模型节点"""

        id = uuid.uuid4()
        start_at = time.perf_counter()
        # 获取配置 LLM
        llm = self.agent_config.llm

        # llm是否支持绑定工具 是否有可以绑定的工具
        if hasattr(llm, "bind_tools") and callable(getattr(llm, "bind_tools")) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)

        # 流式调用模型 获取内容
        gathered = None
        is_first_chunk = True
        generation_type = ""
        for chunk in llm.stream(state["messages"]):
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            # 根据生成的类型 向队列中添加不同事件
            if not generation_type:
                if chunk.tool_calls:
                    generation_type = "thought"
                elif chunk.content:
                    generation_type = "message"

            # 发布智能体消息事件
            if generation_type == "message":
                self.agent_queue_manager.publish(AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=AgentQueueEvent.AGENT_MESSAGE,
                    messages=messages_to_dict(state["messages"]),
                    thought=chunk.content,
                    answer=chunk.content,
                    latency=(time.perf_counter() - start_at)
                ))

        # 发布智能体推理事件
        if generation_type == "thought":
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=id,
                task_id=self.agent_queue_manager.task_id,
                event=QueueEvent.AGENT_THOUGHT,
                messages=messages_to_dict(state["messages"]),
                latency=(time.perf_counter() - start_at)
            ))
        elif generation_type == "message":
            # 7.如果LLM直接生成answer则表示已经拿到了最终答案，则停止监听
            self.agent_queue_manager.stop_listen()

        return {"messages": [gathered]}

    def _tools_node(self, state: AgentState) -> AgentState:
        """工具节点"""

        # 工具映射转换
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        # 提取消息中 工具调用
        tool_calls = state["messages"][-1].tool_calls

        # 循环执行工具 组装工具执行结果
        messages = []
        for tool_call in tool_calls:
            id = uuid.uuid4()
            start_at = time.perf_counter()

            tool = tools_by_name[tool_call["name"]]
            tool_result = tool.invoke(tool_call["args"])
            messages.append(ToolMessage(
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
                content=json.dumps(tool_result),
            ))

            # 判断执行工具的名字，提交不同事件，涵盖智能体动作以及知识库检索
            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != "dataset_retrieval"
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(
                AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=event,
                    observation=json.dumps(tool_result),
                    tool=tool_call["name"],
                    tool_input=tool_call["args"],
                    latency=(time.perf_counter() - start_at),
                )
            )
        return {"messages": messages}

    @classmethod
    def _tools_condition(self, state: AgentState) -> Literal["tools", "__end__"]:
        """检测下一个节点 是否只 tool 节点"""

        # 提取最后一条AI消息
        ai_message = state["messages"][-1]
        # AI消息中如果存在 tools_calls 执行 tool 节点 反之表示结束
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END
