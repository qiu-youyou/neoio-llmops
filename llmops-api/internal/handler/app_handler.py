#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_handle
@Time   :   2025/9/1 11:46
@Author :   s.qiu@foxmail.com
"""
import json
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Dict, Any, Literal, Generator
from uuid import UUID, uuid4

from flask import request
from flask_login import login_required, current_user
from injector import inject
from langchain_classic.base_memory import BaseMemory
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import MessagesState, StateGraph

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import CompletionReq, CreateAppReq, GetAppResp, GetPublishHistoriesWithPageReq, \
    GetPublishHistoriesWithPageResp, FallbackHistoryToDraftReq, UpdateDebugConversationSummaryReq, UpdateAppReq, \
    DebugChatReq, GetDebugConversationMessagesWithPageReq, GetDebugConversationMessagesWithPageResp
from internal.service import AppService, VectorDatabaseService, ConversationService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


@inject
@dataclass
class AppHandler:
    """应用控制器"""
    app_service: AppService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService

    @login_required
    def create_app(self):
        """个人空间新增应用"""
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app = self.app_service.create_app(req, current_user)
        return success_json({"id": app.id})

    @login_required
    def update_app(self, app_id: UUID):
        """更新指定应用信息"""
        req = UpdateAppReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        self.app_service.update_app(app_id, req, current_user)
        return success_message("更新应用成功")

    @login_required
    def delete_app(self, app_id: UUID):
        """删除指定应用"""
        self.app_service.delete_app(app_id, current_user)
        return success_message("删除应用成功")

    @login_required
    def get_app(self, app_id: UUID):
        """获取应用基础信息"""
        app = self.app_service.get_app(app_id, current_user)
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def get_draft_app_config(self, app_id: UUID):
        """获取应用的草稿配置信息"""
        draft_config = self.app_service.get_draft_app_config(app_id, current_user)
        return success_json(draft_config)

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """更新应用草稿配置"""
        draft_app_config = request.get_json(force=True, silent=True) or {}
        self.app_service.update_draft_app_config(app_id, draft_app_config, current_user)
        return success_message("应用草稿配置更新成功")

    @login_required
    def publish_draft_app_config(self, app_id: UUID):
        """发布/更新应用 运行时配置信息"""
        self.app_service.publish_draft_app_config(app_id, current_user)
        return success_message("发布/更新应用成功")

    @login_required
    def cancel_publish_app_config(self, app_id: UUID):
        """取消发布应用"""
        self.app_service.cancel_publish_app_config(app_id, current_user)
        return success_message("取消发布应用成功")

    def fallback_history_to_draft(self, app_id: UUID):
        """应用回退指定配置版本到当前草稿"""
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.app_service.fallback_history_to_draft(app_id, req.app_config_version_id.data, current_user)
        return success_message("已回退版本配置到草稿")

    @login_required
    def get_publish_histories_with_page(self, app_id: UUID):
        req = GetPublishHistoriesWithPageReq(request.args)
        app_config_versions, paginator = self.app_service.get_publish_histories_with_page(app_id, req, current_user)
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(app_config_versions), paginator=paginator))

    @login_required
    def get_debug_conversation_summary(self, app_id: UUID):
        """获取应用会话调试的长期记忆"""
        summary = self.app_service.get_debug_conversation_summary(app_id, current_user)
        return success_json({"summary": summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: UUID):
        """更新应用会话调试的长期记忆"""
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            raise validate_error_json(req.errors)
        self.app_service.update_debug_conversation_summary(app_id, req.summary.data, current_user)
        return success_message("更新长期记忆成功")

    @login_required
    def delete_debug_conversation(self, app_id: UUID):
        """删除应用会话调试记录"""
        self.app_service.delete_debug_conversation(app_id, current_user)
        return success_message("删除会话记录成功")

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig) -> None:
        """存储对应的上下文信息到记忆实体中"""
        # 加载记忆
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory")
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

    @classmethod
    def _load_memory_variables(cls, input: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """加载记忆变量信息"""
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory")
        if configurable_memory is not None and isinstance(configurable_memory, BaseMemory):
            return configurable_memory.load_memory_variables(input)
        return {"history": []}

    @login_required
    def get_debug_conversation_messages_with_page(self, app_id: UUID):
        """获取调试会话消息列表"""
        req = GetDebugConversationMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        messages, paginator = self.app_service.get_debug_conversation_messages_with_page(app_id, req, current_user)
        resp = GetDebugConversationMessagesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))

    @login_required
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

            graph.invoke({"messages": [("human", query)]})
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

    @login_required
    def stop_debug_chat(self, app_id: UUID, task_id: UUID):
        """关闭应用指定任务的调试会话"""
        self.app_service.stop_debug_chat(app_id, task_id, current_user)
        return success_message("应用会话停止调试成功")

    @login_required
    def debug_chat(self, app_id: UUID) -> Generator:
        """应用调试对话"""
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)
        response = self.app_service.debug_chat(app_id, req.query.data, current_user)
        return compact_generate_response(response)

    @login_required
    def ping(self):
        pass
