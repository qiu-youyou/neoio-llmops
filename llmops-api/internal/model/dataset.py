#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   dataset
@Time   :   2025/12/16 14:09
@Author :   s.qiu@foxmail.com
"""

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.extension.database_extension import db


class Dataset(db.Model):
    """知识库表"""
    __tablename__ = "dataset"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class Document(db.Model):
    """文档表模型"""
    __tablename__ = "document"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_document_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    upload_file_id = Column(UUID, nullable=False)
    process_rule_id = Column(UUID, nullable=False)
    batch = Column(String(255), nullable=False, server_default=text("''::character varying"))
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    position = Column(Integer, nullable=False, server_default=text("1"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    processing_started_at = Column(DateTime, nullable=True)
    parsing_completed_at = Column(DateTime, nullable=True)
    splitting_completed_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class Segment(db.Model):
    """片段表模型"""
    __tablename__ = "segment"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_segment_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    document_id = Column(UUID, nullable=False)
    node_id = Column(UUID, nullable=False)
    position = Column(Integer, nullable=False, server_default=text("1"))
    content = Column(Text, nullable=False, server_default=text("''::text"))
    character_count = Column(Integer, nullable=False, server_default=text("0"))
    token_count = Column(Integer, nullable=False, server_default=text("0"))
    keywords = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    hash = Column(String(255), nullable=False, server_default=text("''::character varying"))
    hit_count = Column(Integer, nullable=False, server_default=text("0"))
    enabled = Column(Boolean, nullable=False, server_default=text("false"))
    disabled_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    indexing_completed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=False, server_default=text("''::text"))
    status = Column(String(255), nullable=False, server_default=text("'waiting'::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class KeywordTable(db.Model):
    """关键词表模型"""
    __tablename__ = "keyword_table"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_keyword_table_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    keyword_table = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class DatasetQuery(db.Model):
    """知识库查询表模型"""
    __tablename__ = "dataset_query"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_dataset_query_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(UUID, nullable=False)
    query = Column(Text, nullable=False, server_default=text("''::text"))
    source = Column(String(255), nullable=False, server_default=text("'HitTesting'::character varying"))
    source_app_id = Column(UUID, nullable=True)
    created_by = Column(UUID, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))


class ProcessRule(db.Model):
    """文档处理规则表模型"""
    __tablename__ = "process_rule"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_process_rule_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    mode = Column(String(255), nullable=False, server_default=text("'automic'::character varying"))
    rule = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        server_onupdate=text('CURRENT_TIMESTAMP(0)'),
    )
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP(0)'))
