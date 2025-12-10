#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   api_tool
@Time   :   2025/12/5 15:51
@Author :   s.qiu@foxmail.com
"""

from sqlalchemy import (
    Column,
    UUID,
    text,
    Text,
    String,
    DateTime,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class ApiToolProvider(db.Model):
    """自定义插件提供者"""
    __tablename__ = "api_tool_provider"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_provider_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    openapi_schema = Column(Text, nullable=False, server_default=text("''::text"))
    headers = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)")
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )


class ApiTool(db.Model):
    """自定义插件工具表"""
    __tablename__ = "api_tool"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_tool_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    provider_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    url = Column(String(255), nullable=False, server_default=text("''::character varying"))
    method = Column(String(255), nullable=False, server_default=text("''::character varying"))
    parameters = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)")
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)")
    )
