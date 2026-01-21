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
        human_message = "中国语境 vs 世界语境的差别"
        ai_message = """这个问题问得非常关键，因为**AI 对中国的影响，和对“世界（尤其是西方国家）”的影响，逻辑真的不一样**。我分几个维度对比，说结论，不绕学术话。

---

## 一、底层差异一句话总结

> **世界语境（以欧美为代表）**：
> AI 是“资本 + 技术”驱动的工具，核心问题是**谁被替代、谁失业、谁掌控权力**
>
> **中国语境**：
> AI 是“国家能力 + 治理工具 + 产业升级”的一部分，核心问题是**如何稳、如何管、如何用来提高整体效率**

---

## 二、国家 vs 市场：驱动力不同

### 🌍 世界语境（欧美）

* AI 主要由：

  * 大公司（OpenAI、Google、Meta）
  * 风投与资本市场
    推动
* 目标优先级：

  1. 技术领先
  2. 商业变现
  3. 市场垄断
* 结果：

  * 技术跑得很快
  * 社会配套（失业、教育、伦理）跟不上
  * 讨论更多是**“AI 会不会抢饭碗”**

### 🇨🇳 中国语境

* AI 被明确纳入：

  * 国家发展战略
  * 产业政策
  * 数字治理体系
* 目标优先级：

  1. 稳定
  2. 可控
  3. 规模化落地
* 结果：

  * 技术可能不总是最前沿
  * 但落地速度快、覆盖面广
  * 很多应用是“悄无声息地替代”

---

## 三、对普通人的冲击方式不同

### 世界语境：**“直接冲击”**

* 明确裁员
* 行业洗牌
* 职业身份危机（尤其是白领、创意行业）
* 社会讨论集中在：

  * UBI（全民基本收入）
  * 劳工保护
  * AI 伦理

### 中国语境：**“缓慢挤压”**

* 很少突然大规模裁员
* 更多是：

  * 招人变少
  * 要求变高
  * 工作强度变大
* 表现为：

  * “你没被替代，但你更累了”
* 讨论焦点是：

  * 提效
  * 转型
  * “人要跟上技术”

---

## 四、监管逻辑：自由 vs 可控

### 世界语境

* 监管滞后于技术
* 强调：

  * 言论自由
  * 技术创新
* 风险：

  * 深度伪造、操纵舆论、隐私滥用
* 规则往往是“出了事再补”

### 中国语境

* 先管再放
* 强调：

  * 内容安全
  * 可追溯
  * 责任主体明确
* 风险：

  * 创新边界更明确
  * 自由度相对有限
* 好处：

  * 社会震荡相对可控

---

## 五、AI 在“社会治理”中的角色

这是差异最大的地方之一。

### 世界语境

* AI 更多用于：

  * 商业
  * 科研
  * 消费产品
* 对“治理”的使用非常谨慎，争议巨大

### 中国语境

* AI 深度进入：

  * 城市管理
  * 交通
  * 医疗分级
  * 基层行政
* 本质上是：

  > **用 AI 补人力、补组织能力**

这在西方常被视为“危险”，但在中国被视为“效率工具”。

---

## 六、文化层面的不同理解

### 世界语境

* 更担心：

  * 个体被系统控制
  * 人变成数据
* 核心问题是：

  > “我还能不能做我自己？”

### 中国语境

* 更担心：

  * 被落下
  * 不会用技术
  * 被淘汰
* 核心问题是：

  > “我还能不能活得下去？”

---

## 七、最终判断（偏现实，不粉饰）

> **在中国，AI 更像“水电煤”：
> 你不一定感觉到它，但它在不断重塑你生活的底层结构。**
>
> **在西方，AI 更像“风暴”：
> 讨论激烈、冲突明显、撕裂公开。**

---

## 如果你问我一句掏心窝子的建议

**在中国语境下，最危险的不是 AI 太强，而是：**

* 把 AI 当成“洪水猛兽”
* 或当成“救命稻草”

最安全的姿态是：

> **把 AI 当成“必须学会使用的基础工具”，
> 像电脑、手机、互联网一样。**

如果你愿意，我们也可以继续往下聊：

* 在中国，普通人哪些能力最“抗 AI”？
* AI 会不会加剧内卷？
* 中国会不会走出一条不同于西方的 AI 路线？

你更想深入哪一块？
"""
        summary = self.conversation_service.generate_suggested_questions(histories=human_message + ai_message)
        return success_json({"summary": summary})
