#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset_retrieval_entity
@Time   :   2026/3/5
@Author :   s.qiu@foxmail.com
"""
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType, VariableType
from internal.entity.dataset_entity import RetrievalStrategy
from internal.exception import FailException


class RetrievalConfig(BaseModel):
    """检索配置"""
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC  # 检索策略
    k: int = 4  # 最大召回数量
    score: float = 0  # 得分阈值


class DatasetRetrievalNodeData(BaseNodeData):
    """知识库检索节点"""
    dataset_ids: list[UUID]  # 关联的知识库ID
    retrieval_config: RetrievalConfig = RetrievalConfig()  # 检索配置
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量信息
    outputs: list[VariableEntity] = Field(exclude=True, default_factory=lambda: [
        VariableEntity(name="combine_documents", value={"type": VariableValueType.GENERATED})
    ])

    @field_validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校验输入信息 只允许有一个变量"""
        if len(value) != 1:
            raise FailException("知识库节点输入变量错误")
        # 判断输入的名称及类型是否出错
        query_input = value[0]
        if query_input.name != "query" or query_input.type != VariableType.STRING or query_input.required is False:
            raise FailException("知识库节点输入变量名字/变量类型/必填属性出错")
        return value
