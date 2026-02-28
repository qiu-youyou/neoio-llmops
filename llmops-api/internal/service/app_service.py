#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app_service
@Time   :   2025/9/17 16:21
@Author :   s.qiu@foxmail.com
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from threading import Thread
from typing import Any, Generator
from uuid import UUID

from flask import current_app
from injector import inject
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from redis import Redis
from sqlalchemy import func, desc

from internal.core.agent.agents import FunctionCallAgent, AgentQueueManager
from internal.core.agent.entities import AgentConfig
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.core.memory import TokenBufferMemory
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG
from internal.entity.conversation_entity import InvokeFrom, MessageStatus
from internal.entity.dataset_entity import RetrievalSource
from internal.exception import NotFoundException, ForbiddenException, ValidateErrorException, FailException
from internal.lib.helper import remove_fields
from internal.model import App, Account, AppConfigVersion, ApiTool, Dataset, AppConfig, AppDatasetJoin, Message
from internal.schema.app_schema import CreateAppReq, GetPublishHistoriesWithPageReq, \
    GetDebugConversationMessagesWithPageReq, GetAppsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .app_config_service import AppConfigService
from .base_service import BaseService
from .conversation_service import ConversationService
from .retrieval_service import RetrievalService


@inject
@dataclass
class AppService(BaseService):
    """应用 服务"""
    db: SQLAlchemy
    redis_client: Redis
    app_config_service: AppConfigService
    retrieval_service: RetrievalService
    conversation_service: ConversationService
    builtin_provider_manager: BuiltinProviderManager
    api_provider_manager: ApiProviderManager

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        """个人空间新增应用"""
        with self.db.auto_commit():
            app = App(
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            # 创建APP并刷新数据
            self.db.session.add(app)
            self.db.session.flush()

            app_config_version = AppConfigVersion(
                version=0,
                app_id=app.id,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            # 添加草稿记录
            self.db.session.add(app_config_version)
            self.db.session.flush()
            # 为APP关联草稿配置ID
            app.draft_app_config_id = app_config_version.id
        return app

    def get_app(self, app_id: UUID, account: Account) -> App:
        """获取应用基础信息"""
        app = self.get(App, app_id)
        if not app:
            raise NotFoundException("该应用不存在")
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限！")
        return app

    def delete_app(self, app_id: uuid.UUID, account: Account) -> App:
        """删除指定应用"""
        app = self.get_app(app_id, account)
        self.delete(app)
        return app

    def update_app(self, app_id: uuid.UUID, account: Account, **kwargs) -> App:
        """更新指定应用信息"""
        app = self.get_app(app_id, account)
        self.update(app, **kwargs)
        return app

    def get_apps_with_page(self, req: GetAppsWithPageReq, account: Account) -> tuple[list[App], Paginator]:
        """获取应用分页列表"""
        paginate = Paginator(self.db, req)
        filters = [App.account_id == account.id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))

        apps = paginate.paginate(self.db.session.query(App).filter(*filters).order_by(desc("created_at")))
        return apps, paginate

    def copy_app(self, app_id: uuid.UUID, account: Account) -> App:
        """创建应用副本 拷贝Agent信息创建新Agent"""

        # 获取应用以及应用草稿配置
        app = self.get_app(app_id, account)
        draft_app_config = app.draft_app_config
        # 复制 应用信息、应用草稿配置信息
        app_copy = app.__dict__.copy()
        draft_app_config_copy = draft_app_config.__dict__.copy()

        # 移除不需要拷贝的字段
        app_remove_fields = ["id", "app_config_id", "draft_app_config_id", "debug_conversation_id", "status",
                             "updated_at", "created_at", "_sa_instance_state"]
        draft_app_config_remove_fields = ["id", "app_id", "version", "updated_at", "created_at", "_sa_instance_state"]
        remove_fields(app_copy, app_remove_fields)
        remove_fields(draft_app_config_copy, draft_app_config_remove_fields)

        # 添加到数据库 自动提交上下文
        with self.db.auto_commit():
            new_app = App(**app_copy, status=AppStatus.DRAFT)
            self.db.session.add(new_app)
            self.db.session.flush()

            new_draft_app_config = AppConfigVersion(**draft_app_config_copy, app_id=new_app.id, version=0)
            self.db.session.add(new_draft_app_config)
            self.db.session.flush()

            new_app.draft_app_config_id = new_draft_app_config.id

        return new_app

    def get_draft_app_config(self, app_id: UUID, account: Account) -> dict[str, Any]:
        app = self.get_app(app_id, account)
        return self.app_config_service.get_draft_app_config(app)

    def update_draft_app_config(self, app_id: UUID, draft_app_config: dict[str, Any],
                                account: Account) -> AppConfigVersion:
        """更新应用草稿配置"""
        app = self.get_app(app_id, account)
        # 校验传递的草稿配置
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)
        draft_app_config_record = app.draft_app_config

        # todo: server_onupdate 字段手动传递
        self.update(draft_app_config_record, updated_at=datetime.now(), **draft_app_config)
        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account):
        """发布/更新指定应用草稿配置为运行时配置"""
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 创建应用的运行配置
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=draft_app_config["model_config"],
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            suggested_after_answer=draft_app_config["suggested_after_answer"],
            review_config=draft_app_config["review_config"],
            # todo:等待工作流模块完成
            workflows=draft_app_config["workflows"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],
        )
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 删除原有关联知识库 与新增知识库新型关联
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(AppDatasetJoin.app_id == app.id).delete()

        for dataset in draft_app_config["datasets"]:
            self.create(AppDatasetJoin, app_id=app.id, dataset_id=dataset["id"])

        # 获取应用草稿记录，并移除id、version、config_type、updated_at、created_at字段
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields = ["id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"]
        for field in remove_fields:
            draft_app_config_copy.pop(field)

        # 获取当前最大的发布版本
        max_version = self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0)).filter(
            AppConfigVersion.app_id == app.id,
            AppConfigVersion.config_type == AppConfigType.PUBLISHED
        ).scalar()

        # 新增发布历史 配置信息
        self.create(AppConfigVersion, version=max_version + 1, config_type=AppConfigType.PUBLISHED,
                    **draft_app_config_copy)

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account):
        """取消发布指定应用配置"""
        app = self.get_app(app_id, account)
        if app.status == AppStatus.DRAFT:
            raise FailException("该应用未发布")

        # 修改应用状态到草稿状态啊 清空关联的配置ID
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 清空关联的知识库
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(AppDatasetJoin.app_id == app.id).delete()
        return app

    def fallback_history_to_draft(self, app_id: UUID, app_config_version_id: UUID, account: Account):
        app = self.get_app(app_id, account)
        app_config_version = self.get(AppConfigVersion, app_config_version_id)
        if not app_config_version:
            raise NotFoundException("该历史版本不存在")

        # 校验历史版本配置信息 剔除已删除的工具、知识库、工作流
        draft_app_config_dict = app_config_version.__dict__.copy()
        remove_fields = ["id", "app_id", "version", "config_type", "updated_at", "created_at", "_sa_instance_state"]
        for field in remove_fields:
            draft_app_config_dict.pop(field)
        draft_app_config_dict = self._validate_draft_app_config(draft_app_config_dict, account)

        # 更新草稿配置信息
        draft_app_config_record = app.draft_app_config
        self.update(draft_app_config_record, updated_at=datetime.now(), **draft_app_config_dict)
        return draft_app_config_record

    def get_publish_histories_with_page(self, app_id: UUID, req: GetPublishHistoriesWithPageReq, account: Account):
        """获取应用的发布历史 配置信息 列表"""
        self.get_app(app_id, account)
        paginator = Paginator(db=self.db, req=req)
        filters = [AppConfigVersion.app_id == app_id, AppConfigVersion.config_type == AppStatus.PUBLISHED]
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion).filter(*filters).order_by(desc("version")))

        return app_config_versions, paginator

    def get_debug_conversation_summary(self, app_id: UUID, account: Account):
        """获取应用会话调试的长期记忆"""
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)

        # 应用配置中是否启用长期记忆
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用未开启长期记忆功能")
        return app.debug_conversation.summary

    def update_debug_conversation_summary(self, app_id: UUID, summary: str, account: Account):
        """更新应用会话调试的长期记忆"""
        app = self.get_app(app_id, account)
        # 获取并校验草稿配置信息
        draft_app_config = self.get_draft_app_config(app_id, account)
        # 应用配置中是否启用长期记忆
        if draft_app_config["long_term_memory"]["enable"] is False:
            raise FailException("该应用未开启长期记忆功能")
        # 更新长期记忆
        debug_conversation = app.debug_conversation
        self.update(debug_conversation, summary=summary)
        return debug_conversation

    def delete_debug_conversation(self, app_id: UUID, account: Account):
        """删除应用会话调试记录"""
        app = self.get_app(app_id, account)
        if not app.debug_conversation_id:
            return app
        # 删除与会话的关联
        app = self.update(app, debug_conversation_id=None)
        return app

    def get_debug_conversation_messages_with_page(self, app_id: UUID, req: GetDebugConversationMessagesWithPageReq,
                                                  account: Account):
        """获取调试会话消息列表"""
        app = self.get_app(app_id, account)
        debug_conversation = app.debug_conversation

        paginator = Paginator(db=self.db, req=req)
        filters = [Message.conversation_id == debug_conversation.id,
                   Message.status.in_([MessageStatus.NORMAL, MessageStatus.STOP]),
                   Message.answer != ""]
        if req.created_at.data:
            # 时间戳转换为DateTime
            created_at_datetime = datetime.fromtimestamp(req.created_at.data)
            filters.append(Message.created_at <= created_at_datetime)

        messages = paginator.paginate(self.db.session.query(Message).filter(*filters).order_by(desc("created_at")))
        return messages, paginator

    def stop_debug_chat(self, app_id: UUID, task_id: UUID, account: Account) -> None:
        """关闭应用指定任务的调试会话"""
        self.get_app(app_id, account)
        AgentQueueManager.set_stop_flag(task_id, InvokeFrom.DEBUGGER, account.id)

    def debug_chat(self, app_id: UUID, query: str, account: Account) -> Generator:
        """智能体 会话调试"""

        # 获取应用信息
        app = self.get_app(app_id, account)
        # 获取当前应用 最新草稿配置
        draft_app_config = self.get_draft_app_config(app_id, account)
        # 获取当前应用 会话信息
        debug_conversation = app.debug_conversation

        # 新建消息记录
        message = self.create(Message, app_id=app.id, conversation_id=debug_conversation.id,
                              invoke_from=InvokeFrom.DEBUGGER, created_by=account.id,
                              query=query, status=MessageStatus.NORMAL)

        # 根据配置实例化模型
        llm = ChatOpenAI(model=draft_app_config["model_config"]["model"],
                         **draft_app_config["model_config"]["parameters"])

        # 提取短期记忆
        token_buffer_memory = TokenBufferMemory(db=self.db, conversation=debug_conversation, model_instance=llm)
        history = token_buffer_memory.get_history_prompt_messages(message_limit=draft_app_config["dialog_round"])

        tools = self.app_config_service.get_langchain_tools_by_tools_config(draft_app_config["tools"])

        # 关联知识库 构建 LangChain 知识库检索工具
        if draft_app_config["datasets"]:
            dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
                flask_app=current_app._get_current_object(),
                dataset_ids=[dataset["id"] for dataset in draft_app_config["datasets"]],
                account_id=account.id,
                retrival_source=RetrievalSource.APP,
                **draft_app_config["retrieval_config"],
            )
            tools.append(dataset_retrieval)

        # 构建 AGENT 智能体 使用 FUNCTIONCALLAGENT
        agent = FunctionCallAgent(llm=llm, agent_config=AgentConfig(
            user_id=account.id,
            invoke_from=InvokeFrom.DEBUGGER,
            enable_long_term_memory=draft_app_config["long_term_memory"]["enable"],
            tools=tools,
            review_config=draft_app_config["review_config"],
        ))

        # 执行智能体
        agent_thoughts = {}
        for agent_thought in agent.stream({
            "messages": [HumanMessage(query)],
            "history": history,
            "long_term_memory": debug_conversation.summary,
        }):
            event_id = str(agent_thought.id)

            # agent_thought 填充数据 除 agent_message 外的消息都进行覆盖处理
            if agent_thought.event != QueueEvent.PING:
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    if event_id not in agent_thoughts:
                        agent_thoughts[event_id] = agent_thought
                    else:
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "latency": agent_thought.latency,
                        })
                else:
                    agent_thoughts[event_id] = agent_thought

            data = {
                **agent_thought.model_dump(include={
                    "event", "thought", "observation", "tool", "tool_input", "answer", "latency",
                }),
                "id": event_id,
                "conversation_id": str(debug_conversation.id),
                "message_id": str(message.id),
                "task_id": str(agent_thought.task_id),
            }
            yield f"event: {agent_thought.event}\ndata: {json.dumps(data)}\n\n"

        # 将消息以及推理过程添加到数据库记录
        thread = Thread(target=self.conversation_service.save_agent_thoughts, kwargs={
            "flask_app": current_app._get_current_object(),
            "account_id": account.id,
            "app_id": app_id,
            "app_config": draft_app_config,
            "conversation_id": debug_conversation.id,
            "message_id": message.id,
            "agent_thoughts": [agent_thought for agent_thought in agent_thoughts.values()],
        })
        thread.start()

    def _validate_draft_app_config(self, draft_app_config: dict[str, Any], account: Account) -> dict[str, Any]:
        """校验传递的应用草稿配置信息，返回校验后的数据"""
        # 1.校验上传的草稿配置中对应的字段，至少拥有一个可以更新的配置
        acceptable_fields = [
            "model_config", "dialog_round", "preset_prompt",
            "tools", "workflows", "datasets", "retrieval_config",
            "long_term_memory", "opening_statement", "opening_questions",
            "speech_to_text", "text_to_speech", "suggested_after_answer", "review_config",
        ]

        # 2.判断传递的草稿配置是否在可接受字段内
        if (
                not draft_app_config
                or not isinstance(draft_app_config, dict)
                or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidateErrorException("草稿配置字段出错，请核实后重试")

        # todo:3.校验model_config字段，等待多LLM接入时完成该步骤校验

        # 4.校验dialog_round上下文轮数，校验数据类型以及范围
        if "dialog_round" in draft_app_config:
            dialog_round = draft_app_config["dialog_round"]
            if not isinstance(dialog_round, int) or not (0 <= dialog_round <= 100):
                raise ValidateErrorException("携带上下文轮数范围为0-100")

        # 5.校验preset_prompt
        if "preset_prompt" in draft_app_config:
            preset_prompt = draft_app_config["preset_prompt"]
            if not isinstance(preset_prompt, str) or len(preset_prompt) > 2000:
                raise ValidateErrorException("人设与回复逻辑必须是字符串，长度在0-2000个字符")

        # 6.校验tools工具
        if "tools" in draft_app_config:
            tools = draft_app_config["tools"]
            validate_tools = []

            # 6.1 tools类型必须为列表，空列表则代表不绑定任何工具
            if not isinstance(tools, list):
                raise ValidateErrorException("工具列表必须是列表型数据")
            # 6.2 tools的长度不能超过5
            if len(tools) > 5:
                raise ValidateErrorException("Agent绑定的工具数不能超过5")
            # 6.3 循环校验工具里的每一个参数
            for tool in tools:
                # 6.4 校验tool非空并且类型为字典
                if not tool or not isinstance(tool, dict):
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.5 校验工具的参数是不是type、provider_id、tool_id、params
                if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.6 校验type类型是否为builtin_tool以及api_tool
                if tool["type"] not in ["builtin_tool", "api_tool"]:
                    raise ValidateErrorException("绑定插件工具参数出错")
                # 6.7 校验provider_id和tool_id
                if (
                        not tool["provider_id"]
                        or not tool["tool_id"]
                        or not isinstance(tool["provider_id"], str)
                        or not isinstance(tool["tool_id"], str)
                ):
                    raise ValidateErrorException("插件提供者或者插件标识参数出错")
                # 6.8 校验params参数，类型为字典
                if not isinstance(tool["params"], dict):
                    raise ValidateErrorException("插件自定义参数格式错误")
                # 6.9 校验对应的工具是否存在，而且需要划分成builtin_tool和api_tool
                if tool["type"] == "builtin_tool":
                    builtin_tool = self.builtin_provider_manager.get_tool(tool["provider_id"], tool["tool_id"])
                    if not builtin_tool:
                        continue
                else:
                    api_tool = self.db.session.query(ApiTool).filter(
                        ApiTool.provider_id == tool["provider_id"],
                        ApiTool.name == tool["tool_id"],
                        ApiTool.account_id == account.id,
                    ).one_or_none()
                    if not api_tool:
                        continue

                validate_tools.append(tool)

            # 6.10 校验绑定的工具是否重复
            check_tools = [f"{tool['provider_id']}_{tool['tool_id']}" for tool in validate_tools]
            if len(set(check_tools)) != len(validate_tools):
                raise ValidateErrorException("绑定插件存在重复")

            # 6.11 重新赋值工具
            draft_app_config["tools"] = validate_tools

        # todo:7.校验workflows，等待工作流模块完成后实现
        if "workflows" in draft_app_config:
            draft_app_config["workflows"] = []

        # 8.校验datasets知识库列表
        if "datasets" in draft_app_config:
            datasets = draft_app_config["datasets"]

            # 8.1 判断datasets类型是否为列表
            if not isinstance(datasets, list):
                raise ValidateErrorException("绑定知识库列表参数格式错误")
            # 8.2 判断关联的知识库列表是否超过5个
            if len(datasets) > 5:
                raise ValidateErrorException("Agent绑定的知识库数量不能超过5个")
            # 8.3 循环校验知识库的每个参数
            for dataset_id in datasets:
                try:
                    UUID(dataset_id)
                except Exception as e:
                    raise ValidateErrorException("知识库列表参数必须是UUID")
            # 8.4 判断是否传递了重复的知识库
            if len(set(datasets)) != len(datasets):
                raise ValidateErrorException("绑定知识库存在重复")
            # 8.5 校验绑定的知识库权限，剔除不属于当前账号的知识库
            dataset_records = self.db.session.query(Dataset).filter(
                Dataset.id.in_(datasets),
                Dataset.account_id == account.id,
            ).all()
            dataset_sets = set([str(dataset_record.id) for dataset_record in dataset_records])
            draft_app_config["datasets"] = [dataset_id for dataset_id in datasets if dataset_id in dataset_sets]

        # 9.校验retrieval_config检索配置
        if "retrieval_config" in draft_app_config:
            retrieval_config = draft_app_config["retrieval_config"]

            # 9.1 判断检索配置非空且类型为字典
            if not retrieval_config or not isinstance(retrieval_config, dict):
                raise ValidateErrorException("检索配置格式错误")
            # 9.2 校验检索配置的字段类型
            if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
                raise ValidateErrorException("检索配置格式错误")
            # 9.3 校验检索策略是否正确
            if retrieval_config["retrieval_strategy"] not in ["semantic", "full_text", "hybrid"]:
                raise ValidateErrorException("检测策略格式错误")
            # 9.4 校验最大召回数量
            if not isinstance(retrieval_config["k"], int) or not (0 <= retrieval_config["k"] <= 10):
                raise ValidateErrorException("最大召回数量范围为0-10")
            # 9.5 校验得分/最小匹配度
            if not isinstance(retrieval_config["score"], float) or not (0 <= retrieval_config["score"] <= 1):
                raise ValidateErrorException("最小匹配范围为0-1")

        # 10.校验long_term_memory长期记忆配置
        if "long_term_memory" in draft_app_config:
            long_term_memory = draft_app_config["long_term_memory"]

            # 10.1 校验长期记忆格式
            if not long_term_memory or not isinstance(long_term_memory, dict):
                raise ValidateErrorException("长期记忆设置格式错误")
            # 10.2 校验长期记忆属性
            if (
                    set(long_term_memory.keys()) != {"enable"}
                    or not isinstance(long_term_memory["enable"], bool)
            ):
                raise ValidateErrorException("长期记忆设置格式错误")

        # 11.校验opening_statement对话开场白
        if "opening_statement" in draft_app_config:
            opening_statement = draft_app_config["opening_statement"]

            # 11.1 校验对话开场白类型以及长度
            if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
                raise ValidateErrorException("对话开场白的长度范围是0-2000")

        # 12.校验opening_questions开场建议问题列表
        if "opening_questions" in draft_app_config:
            opening_questions = draft_app_config["opening_questions"]

            # 12.1 校验是否为列表，并且长度不超过3
            if not isinstance(opening_questions, list) or len(opening_questions) > 3:
                raise ValidateErrorException("开场建议问题不能超过3个")
            # 12.2 开场建议问题每个元素都是一个字符串
            for opening_question in opening_questions:
                if not isinstance(opening_question, str):
                    raise ValidateErrorException("开场建议问题必须是字符串")

        # 13.校验speech_to_text语音转文本
        if "speech_to_text" in draft_app_config:
            speech_to_text = draft_app_config["speech_to_text"]

            # 13.1 校验语音转文本格式
            if not speech_to_text or not isinstance(speech_to_text, dict):
                raise ValidateErrorException("语音转文本设置格式错误")
            # 13.2 校验语音转文本属性
            if (
                    set(speech_to_text.keys()) != {"enable"}
                    or not isinstance(speech_to_text["enable"], bool)
            ):
                raise ValidateErrorException("语音转文本设置格式错误")

        # 14.校验text_to_speech文本转语音设置
        if "text_to_speech" in draft_app_config:
            text_to_speech = draft_app_config["text_to_speech"]

            # 14.1 校验字典格式
            if not isinstance(text_to_speech, dict):
                raise ValidateErrorException("文本转语音设置格式错误")
            # 14.2 校验字段类型
            if (
                    set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                    or not isinstance(text_to_speech["enable"], bool)
                    # todo:等待多模态Agent实现时添加音色
                    or text_to_speech["voice"] not in ["echo"]
                    or not isinstance(text_to_speech["auto_play"], bool)
            ):
                raise ValidateErrorException("文本转语音设置格式错误")

        # 15 校验回答后生成建议问题
        if "suggested_after_answer" in draft_app_config:
            suggested_after_answer = draft_app_config["suggested_after_answer"]

            # 15.1 校验回答后建议问题格式
            if not suggested_after_answer or not isinstance(suggested_after_answer, dict):
                raise ValidateErrorException("回答后建议问题设置格式错误")
            # 15.2 校验回答后建议问题格式
            if (
                    set(suggested_after_answer.keys()) != {"enable"}
                    or not isinstance(suggested_after_answer["enable"], bool)
            ):
                raise ValidateErrorException("回答后建议问题设置格式错误")

        # 16.校验review_config审核配置
        if "review_config" in draft_app_config:
            review_config = draft_app_config["review_config"]

            # 16.1 校验字段格式，非空
            if not review_config or not isinstance(review_config, dict):
                raise ValidateErrorException("审核配置格式错误")
            # 16.2 校验字段信息
            if set(review_config.keys()) != {"enable", "keywords", "inputs_config", "outputs_config"}:
                raise ValidateErrorException("审核配置格式错误")
            # 16.3 校验enable
            if not isinstance(review_config["enable"], bool):
                raise ValidateErrorException("review.enable格式错误")
            # 16.4 校验keywords
            if (
                    not isinstance(review_config["keywords"], list)
                    or (review_config["enable"] and len(review_config["keywords"]) == 0)
                    or len(review_config["keywords"]) > 100
            ):
                raise ValidateErrorException("review.keywords非空且不能超过100个关键词")
            for keyword in review_config["keywords"]:
                if not isinstance(keyword, str):
                    raise ValidateErrorException("review.keywords敏感词必须是字符串")
            # 16.5 校验inputs_config输入配置
            if (
                    not review_config["inputs_config"]
                    or not isinstance(review_config["inputs_config"], dict)
                    or set(review_config["inputs_config"].keys()) != {"enable", "preset_response"}
                    or not isinstance(review_config["inputs_config"]["enable"], bool)
                    or not isinstance(review_config["inputs_config"]["preset_response"], str)
            ):
                raise ValidateErrorException("review.inputs_config必须是一个字典")
            # 16.6 校验outputs_config输出配置
            if (
                    not review_config["outputs_config"]
                    or not isinstance(review_config["outputs_config"], dict)
                    or set(review_config["outputs_config"].keys()) != {"enable"}
                    or not isinstance(review_config["outputs_config"]["enable"], bool)
            ):
                raise ValidateErrorException("review.outputs_config格式错误")
            # 16.7 在开启审核模块的时候，必须确保inputs_config或者是outputs_config至少有一个是开启的
            if review_config["enable"]:
                if (
                        review_config["inputs_config"]["enable"] is False
                        and review_config["outputs_config"]["enable"] is False
                ):
                    raise ValidateErrorException("输入审核和输出审核至少需要开启一项")

                if (
                        review_config["inputs_config"]["enable"]
                        and review_config["inputs_config"]["preset_response"].strip() == ""
                ):
                    raise ValidateErrorException("输入审核预设响应不能为空")

        return draft_app_config
