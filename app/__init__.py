import logging
from datetime import timedelta
from flask import Flask, Response
from flask.globals import g
from flask_jwt_extended import JWTManager
from app.constants import message, ErrorCode
from app.util import resp, JSONProvider
from util.config import uri, dev
from util.database import db
from . import test, user, flag

log = logging.getLogger(__name__)


# proxy_info = LocalProxy(ContextVar("flask.request_ctx"), 'info')


def init(_app: Flask):
    @_app.before_request
    def before():
        """设置语言"""
        g.language = 'zh'
        ...

    @_app.after_request
    def after(response: Response):
        return response

    @_app.errorhandler(Exception)
    def error(e: BaseException):
        log.exception(e)
        if dev:
            return resp(f'{e}', ErrorCode.base_error), getattr(e, 'code', 500)
        else:
            return resp(message.system_error, ErrorCode.base_error), getattr(e, 'code', 500)


def create_app() -> Flask:
    _app = Flask(__name__)
    _app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_POOL_SIZE'] = 100  # 连接池大小
    _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 事务自动提交
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
db.init_app(app)
JWTManager(app)
init(app)


if __name__ == '__main__':
    print(app.url_map)
