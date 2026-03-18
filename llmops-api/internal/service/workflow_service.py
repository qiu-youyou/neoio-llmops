#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_service
@Time   :   2026/3/15 20:50
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.core.workflow.entities.node_entity import NodeType, BaseNodeData
from internal.core.workflow.nodes import (
    CodeNodeData,
    DatasetRetrievalNodeData,
    EndNodeData,
    HttpRequestNodeData,
    LLMNodeData,
    StartNodeData,
    TemplateTransformNodeData,
    ToolNodeData,
)
from internal.entity.workflow_entity import DEFAULT_WORKFLOW_CONFIG, WorkflowStatus
from internal.exception import ValidateErrorException, NotFoundException, ForbiddenException
from internal.model import Workflow, Account, Dataset, ApiTool
from internal.schema.workflow_schema import CreateWorkflowReq, GetWorkflowsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.workflow.entities.edge_entity import BaseEdgeData
from ..lib.helper import convert_model_to_dict


@inject
@dataclass
class WorkflowService(BaseService):
    """工作流服务"""
    db: SQLAlchemy
    builtin_provider_manager: BuiltinProviderManager

    def create_workflow(self, req: CreateWorkflowReq, account: Account) -> Workflow:
        """创建工作流"""
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == req.tool_call_name.data.strip(),
            Workflow.account_id == account.id
        ).one_or_none()
        if check_workflow:
            raise ValidateErrorException("当前账号下已经存在同名的工作流")
        return self.create(Workflow, **{
            **req.data,
            **DEFAULT_WORKFLOW_CONFIG,
            "account_id": account.id,
            "is_debug_passed": False,
            "status": WorkflowStatus.DRAFT,
            "tool_call_name": req.tool_call_name.data.strip(),
        })

    def get_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """获取工作流信息"""
        workflow = self.get(Workflow, workflow_id)
        if not workflow:
            raise NotFoundException("工作流不存在")
        if workflow.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用")
        return workflow

    def delete_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """删除工作流"""
        workflow = self.get_workflow(workflow_id, account)
        self.delete(workflow)
        return workflow

    def update_workflow(self, workflow_id: UUID, account: Account, **kwargs) -> Workflow:
        """更新工作流"""
        workflow = self.get_workflow(workflow_id, account)

        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == kwargs.get("tool_call_name", "").strip(),
            Workflow.account_id == account.id,
            Workflow.id == workflow_id,
        ).one_or_none()
        if check_workflow:
            raise ValidateErrorException("当前账号下已经存在同名的工作流")
        workflow = self.update(workflow, **kwargs)
        return workflow

    def get_workflows_with_page(self, req: GetWorkflowsWithPageReq, account: Account) -> tuple[
        list[Workflow], Paginator]:
        """获取工作流分页接口列表"""
        paginator = Paginator(db=self.db, req=req)
        filters = [Workflow.account_id == account.id]
        if req.search_word.data:
            filters.append(Workflow.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(Workflow.status == req.status.data)

        workflows = paginator.paginate(
            self.db.session.query(Workflow).filter(*filters).order_by(desc("created_at"))
        )
        return workflows, paginator

    def _validate_graph(self, graph: dict[str, Any], account: Account) -> dict[str, Any]:
        """校验传递的graph信息，涵盖nodes和edges对应的数据，该函数使用相对宽松的校验方式，并且因为是草稿，不需要校验节点与边的关系"""
        # 提取nodes和edges数据
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # 构建节点类型与节点数据类映射
        node_data_classes = {
            NodeType.CODE: CodeNodeData,
            NodeType.DATASET_RETRIEVAL: DatasetRetrievalNodeData,
            NodeType.END: EndNodeData,
            NodeType.HTTP_REQUEST: HttpRequestNodeData,
            NodeType.LLM: LLMNodeData,
            NodeType.START: StartNodeData,
            NodeType.TEMPLATE_TRANSFORM: TemplateTransformNodeData,
            NodeType.TOOL: ToolNodeData,
        }

        # 循环校验nodes中各个节点对应的数据
        node_data_dict: dict[UUID, BaseNodeData] = {}
        start_nodes = 0
        end_nodes = 0
        for node in nodes:
            try:
                # 校验传递的node数据是不是字典，如果不是则跳过当前数据
                if not isinstance(node, dict):
                    raise ValidateErrorException("工作流节点数据类型出错")

                # 提取节点的node_type类型，并判断类型是否正确
                node_type = node.get("node_type", "")
                node_data_cls = node_data_classes.get(node_type, None)
                if node_data_cls is None:
                    raise ValidateErrorException("工作流节点类型出错")

                # 实例化节点数据类型，如果出错则跳过当前数据
                node_data = node_data_cls(**node)

                # 判断节点id是否唯一，如果不唯一，则将当前节点清除
                if node_data.id in node_data_dict:
                    raise ValidateErrorException("工作流节点id必须唯一")

                # 判断节点title是否唯一，如果不唯一，则将当前节点清除
                if any(item.title.strip() == node_data.title.strip() for item in node_data_dict.values()):
                    raise ValidateErrorException("工作流节点title必须唯一")

                # 对特殊节点进行判断，涵盖开始/结束/知识库检索/工具
                if node_data.node_type == NodeType.START:
                    if start_nodes >= 1:
                        raise ValidateErrorException("工作流中只允许有1个开始节点")
                    start_nodes += 1
                elif node_data.node_type == NodeType.END:
                    if end_nodes >= 1:
                        raise ValidateErrorException("工作流中只允许有1个结束节点")
                    end_nodes += 1
                elif node_data.node_type == NodeType.DATASET_RETRIEVAL:
                    # 剔除关联知识库列表中不属于当前账户的数据
                    datasets = self.db.session.query(Dataset).filter(
                        Dataset.id.in_(node_data.dataset_ids[:5]),
                        Dataset.account_id == account.id,
                    ).all()
                    node_data.dataset_ids = [dataset.id for dataset in datasets]
                elif node_data.node_type == NodeType.TOOL:
                    # 判断工具的类型执行不同的操作
                    if node_data.tool_type == "builtin_tool":
                        tool = self.builtin_provider_manager.get_tool(node_data.provider_id, node_data.tool_id)
                        if not tool:
                            raise ValidateErrorException("工具节点绑定的内置工具不存在")
                    else:
                        # API工具，查询当前工具是否属于当前账号
                        tool_record = self.db.session.query(ApiTool).filter(
                            ApiTool.provider_id == node_data.provider_id,
                            ApiTool.name == node_data.tool_id,
                            ApiTool.account_id == account.id,
                        ).one_or_none()
                        if not tool_record:
                            raise ValidateErrorException("工具节点绑定的API工具不存在")

                # 将数据添加到node_data_dict中
                node_data_dict[node_data.id] = node_data
            except Exception:
                continue

        # 循环校验edges中各个节点对应的数据
        edge_data_dict: dict[UUID, BaseEdgeData] = {}
        for edge in edges:
            try:
                # 边类型为非字典则抛出错误，否则转换成BaseEdgeData
                if not isinstance(edge, dict):
                    raise ValidateErrorException("工作流边数据类型出错")
                edge_data = BaseEdgeData(**edge)

                # 校验边edges的id是否唯一
                if edge_data.id in edge_data_dict:
                    raise ValidateErrorException("工作流边数据id必须唯一")

                # 校验边中的source/target/source_type/target_type必须和nodes对得上
                if (
                        edge_data.source not in node_data_dict
                        or edge_data.source_type != node_data_dict[edge_data.source].node_type
                        or edge_data.target not in node_data_dict
                        or edge_data.target_type != node_data_dict[edge_data.target].node_type
                ):
                    raise ValidateErrorException("工作流边起点/终点对应的节点不存在或类型错误")

                # 校验边Edges里的边必须唯一(source+target必须唯一)
                if any(
                        (item.source == edge_data.source and item.target == edge_data.target)
                        for item in edge_data_dict.values()
                ):
                    raise ValidateErrorException("工作流边数据不能重复添加")

                # 基础数据校验通过，将数据添加到edge_data_dict中
                edge_data_dict[edge_data.id] = edge_data
            except Exception:
                continue

        return {
            "nodes": [convert_model_to_dict(node_data) for node_data in node_data_dict.values()],
            "edges": [convert_model_to_dict(edge_data) for edge_data in edge_data_dict.values()],
        }
