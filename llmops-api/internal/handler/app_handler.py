#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
import json
from dataclasses import dataclass
from operator import itemgetter
from queue import Queue
from threading import Thread
from typing import Dict, Any, Literal, Generator
from uuid import UUID, uuid4

from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.messages import ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnablePassthrough, RunnableLambda
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import MessagesState, StateGraph

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import CompletionReq
from internal.service import AppService, VectorDatabaseService, ConversationService
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    """应用控制器"""
    app_service: AppService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService

    def get_app(self, id: UUID):
        """查询APP记录"""
        app = self.app_service.get_app(id)
        return success_message(f"查询成功，name 为 {app.name}")

    def create_app(self):
        """创建APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用创建成功, id 为 {app.id}")

    def update_app(self, id: UUID):
        """更新APP记录"""
        app = self.app_service.update_app(id)
        return success_message(f"应用更新成功，修改后 name 为 {app.name}")

    def delete_app(self, id: UUID):
        """删除APP记录"""
        app = self.app_service.delete_app(id)
        return success_message(f"应用删除成功, id 为 {app.id}", )

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储对应的上下文信息到记忆实体中"""
        # 加载记忆
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加载记忆变量信息"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    def _debug(self, app_id: UUID):
        """聊天接口"""
        # 校验接口参数
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 提示词与记忆
        system_prompt = "你是一个强大的聊天机器人，能根据对应的上下文和历史对话信息回复用户问题。\n\n<context>{context}</context>"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{query}"),
        ])

        memory = ConversationBufferWindowMemory(
            k=3,
            input_key="query",
            output_key="output",
            return_messages=True,
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

        # 创建 LLM
        llm = ChatOpenAI(model="kimi-k2-0905-preview")

        retriever = self.vector_database_service.get_retriever() | self.vector_database_service.combine_documents

        # 创建调用链
        chain = (RunnablePassthrough.assign(
            history=RunnableLambda(self._load_memory_variables) | itemgetter("history"),
            context=itemgetter("query") | retriever,
        ) | prompt | llm | StrOutputParser()).with_listeners(on_end=self._save_context)

        chain_input = {"query": req.query.data}
        content = chain.invoke(chain_input, config={"configurable": {"memory": memory}})

        return success_json({"content": content})

    def debug(self, app_id: UUID):
        """聊天调试接口"""
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 创建队列
        q = Queue()
        query = req.query.data

        # 创建 graph 图程序
        def graph_app() -> None:
            # 创建 tools 工具列表
            tools = [
                self.builtin_provider_manager.get_tool("google", "google_serper")(),
                self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
                self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
            ]

            # 创建聊天、工具、路由节点

            def chatbot(state: MessagesState) -> MessagesState:
                """聊天对话节点"""
                llm = ChatOpenAI(model="kimi-k2-0905-preview", temperature=0.7).bind_tools(tools)

                # 获取流式输出内容
                is_first_chunk = True  # 是否是第一个块
                is_tool_call = False  # 是否是工具调用
                gathered = None
                gid = str(uuid4())
                for chunk in llm.stream(state["messages"]):
                    # 一般第一个块不会生成内容 需要抛弃
                    if is_first_chunk and chunk.content == "" and not chunk.tool_calls:
                        continue
                    # 叠加相应区块
                    if is_first_chunk:
                        gathered = chunk
                        is_first_chunk = False
                    else:
                        gathered += chunk

                    # 判断是工具调用还是文本生成，在队列中添加不同数据
                    if chunk.tool_calls or is_tool_call:
                        is_tool_call = True
                        q.put({"id": gid, "event": "agent_thought", "data": json.dumps(chunk.tool_call_chunks)})
                    else:
                        q.put({"id": gid, "event": "agent_message", "data": chunk.content})

                return {"messages": [gathered]}

            def tool_executor(state: MessagesState) -> MessagesState:
                """工具/函数节点"""
                # 提取数据中的 tool_calls
                tool_calls = state["messages"][-1].tool_calls
                # 工具列表转换为字典
                tools_by_name = {tool.name: tool for tool in tools}

                # 执行工具函数获取结果
                message = []
                for tool_call in tool_calls:
                    tid = str(uuid4())
                    tool = tools_by_name[tool_call["name"]]
                    tool_result = tool.invoke(tool_call["args"])
                    message.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=json.dumps(tool_result),
                        tool_name=tool_call["name"],
                    ))
                    q.put({"id": tid, "event": "agent_action", "data": json.dumps(tool_result)})

                return {"messages": message}

            def route(state: MessagesState) -> Literal["tool_executor", "__end__"]:
                """路由节点 用于确认下一步"""
                ai_message = state["messages"][-1]
                if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                    return "tool_executor"
                return END

            # 创建状态图
            graph_builder = StateGraph(MessagesState)
            # 添加节点
            graph_builder.add_node("llm", chatbot)
            graph_builder.add_node("tool_executor", tool_executor)
            # 添加边
            graph_builder.set_entry_point("llm")
            graph_builder.add_conditional_edges("llm", route)
            graph_builder.add_edge("tool_executor", "llm")

            graph = graph_builder.compile()

            result = graph.invoke({"messages": [("human", query)]})
            q.put(None)

        def stream_event_response() -> Generator:
            """流式输出事件"""
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"event: {item.get('event')}\ndata: {json.dumps(item)}\n\n"
                q.task_done()

        t = Thread(target=graph_app)
        t.start()

        return compact_generate_response(stream_event_response())

    def ping(self):
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI

        agent = FunctionCallAgent(AgentConfig(
            llm=ChatOpenAI(model="kimi-k2-0905-preview"),
            preset_prompt="你是一个拥有20年经验的诗人，请根据用户提供的主题来写一首诗"
        ))
        state = agent.run("春天", [], "")
        content = state["messages"][-1].content

        return success_json({"content": content})
