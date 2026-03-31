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
from pkg.response import validate_error_json, success_json, success_message, compact_generate_response


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

    @login_required
    def update_draft_graph(self, workflow_id: UUID):
        """更新工作流草稿配置"""
        # 提取请求的JSON数据
        draft_graph_dict = request.get_json(force=True, silent=True) or {"nodes": [], "edges": []}
        print(draft_graph_dict)
        self.workflow_service.update_draft_graph(workflow_id, draft_graph_dict, current_user)
        return success_message("更新工作流草稿成功")

    @login_required
    def get_draft_graph(self, workflow_id: UUID):
        """获取工作流草稿配置信息"""
        draft_graph = self.workflow_service.get_draft_graph(workflow_id, current_user)
        return success_json(draft_graph)

    @login_required
    def debug_workflow(self, workflow_id: UUID):
        """调试指定的工作流"""
        # 提取用户传递的输入变量信息
        inputs = request.get_json(force=True, silent=True) or {}
        response = self.workflow_service.debug_workflow(workflow_id, inputs, current_user)
        return compact_generate_response(response)

    @login_required
    def publish_workflow(self, workflow_id: UUID):
        """发布指定工作流"""
        self.workflow_service.publish_workflow(workflow_id, current_user)
        return success_message("工作流发布成功")

    @login_required
    def cancel_publish_workflow(self, workflow_id: UUID, ):
        """取消发布指定工作流"""
        self.workflow_service.cancel_publish_workflow(workflow_id, current_user)
        return success_message("工作流取消发布成功")
