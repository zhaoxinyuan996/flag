import logging
from datetime import timedelta
from psycopg2 import errors as pg_errors
from flask import Flask, Response
from flask.globals import g
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
from sqlalchemy import exc
from . import test, user, flag, message
from app.constants import RespMsg, AppError
from app.util import resp, JSONProvider
from util.config import uri, dev
from util.database import db


log = logging.getLogger(__name__)


# proxy_info = LocalProxy(ContextVar("flask.request_ctx"), 'info')
e_code = 500


def init(_app: Flask):
    @_app.before_request
    def before():
        """设置语言"""
        g.language = 'zh'
        ...

    @_app.after_request
    def after(response: Response):
        # 基于请求的自动提交
        db.session.commit()
        return response

    @_app.errorhandler(Exception)
    def error(e: BaseException):
        if isinstance(e, ValidationError):
            return resp(RespMsg.params_error), getattr(e, 'code', e_code)
        elif isinstance(e, exc.IntegrityError):
            if isinstance(e.orig, pg_errors.UniqueViolation):
                return resp(RespMsg.already_exist), e_code
            return resp(RespMsg.database_error), e_code
        elif isinstance(e, AppError):
            return resp(e.msg), e_code
        log.exception(e)
        if dev:
            return resp(str(e)), getattr(e, 'code', e_code)
        return resp(RespMsg.system_error), getattr(e, 'code', e_code)


def create_app() -> Flask:
    _app = Flask(__name__)
    _app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_POOL_SIZE'] = 100  # 连接池大小
    # _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # flask2.3被移除
    # _app.config['SQLALCHEMY_ECHO'] = True
    _app.config["JWT_SECRET_KEY"] = "yes?"  # 设置 jwt 的秘钥
    _app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=9999)
    # 设置刷新JWT过期时间
    _app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    _app.json = JSONProvider(_app)
    return _app


app = create_app()
# 注册蓝图
app.register_blueprint(test.bp)
app.register_blueprint(user.bp)
app.register_blueprint(flag.bp)
app.register_blueprint(message.bp)
db.init_app(app)
JWTManager(app)
init(app)


if __name__ == '__main__':
    print(app.url_map)
