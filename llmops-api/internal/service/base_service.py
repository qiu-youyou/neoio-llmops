#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   base_service
@Time   :   2025/12/9 15:45
@Author :   s.qiu@foxmail.com
"""

from typing import Any, Optional

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


class BaseService:
    """基础服务 完善数据库的基础增删改查功能 以简化代码"""
    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        """根据模型+键值对 创建数据库记录"""
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)
        return model_instance

    def delete(self, model_instance: Any) -> Any:
        """根据传递的模型实例删除数据库记录"""
        with self.db.auto_commit():
            self.db.session.delete(model_instance)
        return model_instance

    def update(self, model_instance: Any, **kwargs) -> Any:
        """根据传递的模型实例+键值对信息更新数据库记录"""
        with self.db.auto_commit():
            for field, value in kwargs.items():
                if hasattr(model_instance, field):
                    setattr(model_instance, field, value)
                else:
                    raise FailException("更新失败")
        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        """根据模型类+主键 获取唯一数据"""
        return self.db.session.query(model).get(primary_key)
