#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app
@Time   :   2025/9/17 15:01
@Author :   s.qiu@foxmail.com
"""

from sqlalchemy import (UUID, Index, Column, String, Text, DateTime, PrimaryKeyConstraint, text)

from internal.extension.database_extension import db


class App(db.Model):
    """基础模型类"""

    __tablename__ = "app"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id", ),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::character varying"))
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))
    remarks = Column(Text, nullable=False, server_default=text("''::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"))
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
