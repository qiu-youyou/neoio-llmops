#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   loggin_extension
@Time   :   2025/12/16 13:39
@Author :   s.qiu@foxmail.com
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler


def init_app(app):
    """日期记录器"""

    # 日志储存的位置
    log_folder = os.path.join(os.getcwd(), "storage", "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_file = os.path.join(log_folder, "app.log")

    # 每天更新一次日志
    handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    # 在开发环境下同时将日志输出到控制台
    if app.debug or os.getenv("FLASK_ENV") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
