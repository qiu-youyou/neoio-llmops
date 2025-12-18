#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   celery_extension
@Time   :   2025/12/17 15:36
@Author :   s.qiu@foxmail.com
"""
from celery import Celery, Task
from flask import Flask


def init_app(app: Flask):
    """初始化 celery """

    class FlaskTask(Task):
        """FlaskTask 确保 Celery 运行在上下文"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 创建配置Celery
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    # 挂载 app 扩展
    app.extensions["celery"] = celery_app
