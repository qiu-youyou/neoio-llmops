#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_service
@Time   :   2026/3/15 20:50
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.workflow_entity import DEFAULT_WORKFLOW_CONFIG, WorkflowStatus
from internal.exception import ValidateErrorException, NotFoundException, ForbiddenException
from internal.model import Workflow, Account
from internal.schema.workflow_schema import CreateWorkflowReq, GetWorkflowsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


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
