#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   workflow_handler
@Time   :   2026/3/15
@Author :   s.qiu@foxmail.com
"""

from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.workflow_schema import CreateWorkflowReq, UpdateWorkflowReq, GetWorkflowResp, \
    GetWorkflowsWithPageReq, GetWorkflowsWithPageResp
from internal.service import WorkflowService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class WorkflowHandler:
    """工作流处理器"""
    workflow_service: WorkflowService

    @login_required
    def create_workflow(self):
        """创建工作流"""
        req = CreateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)
        workflow = self.workflow_service.create_workflow(req, current_user)
        return success_json({"workflow_id": workflow.id})

    @login_required
    def delete_workflow(self, workflow_id: UUID):
        """删除工作流"""
        self.workflow_service.delete_workflow(workflow_id, current_user)
        return success_message("删除成功")

    @login_required
    def update_workflow(self, workflow_id: UUID):
        """更新工作流"""
        req = UpdateWorkflowReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.workflow_service.update_workflow(workflow_id, current_user, **req.data)
        return success_message("更新成功")

    @login_required
    def get_workflow(self, workflow_id: UUID):
        """获取工作流信息"""
        workflow = self.workflow_service.get_workflow(workflow_id, current_user)
        resp = GetWorkflowResp()
        return success_json(resp.dump(workflow))

    @login_required
    def get_workflows_with_page(self):
        """获取工作流分页列表"""
        req = GetWorkflowsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)
        workflows, paginator = self.workflow_service.get_workflows_with_page(req, current_user)
        resp = GetWorkflowsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(workflows), paginator=paginator))
