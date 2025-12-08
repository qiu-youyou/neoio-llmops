#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File   :   app
@Time   :   2025/9/1 13:59
@Author :   s.qiu@foxmail.com
"""
import dotenv
from flask_migrate import Migrate
from injector import Injector

from config import Config
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import ExtensionModule

# 加载ENV到环境变量
dotenv.load_dotenv()

injector = Injector([ExtensionModule])

# 加载配置
conf = Config()

app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router),
)

if __name__ == "__main__":
    app.run(debug=True)
