#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app
@Time   :   2025/9/1 13:59
@Author :   s.qiu@foxmail.com
"""
import dotenv
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import injector

# 加载ENV到环境变量
dotenv.load_dotenv()

# 加载配置
conf = Config()

app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    middleware=injector.get(Middleware),
    login_manager=injector.get(LoginManager),
    router=injector.get(Router),
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=True)
