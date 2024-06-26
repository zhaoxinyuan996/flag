import logging

from datetime import timedelta
from psycopg2 import errors as pg_errors
from flask import Flask, Response
from flask.globals import g
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
from sqlalchemy import exc
from app.constants import RespMsg, AppError, JwtConfig
from app.util import resp, JSONProvider, werkzeug_profile
from util.config import redis_uri, db_uri, dev, config
from util.database import db, redis_cli


log = logging.getLogger(__name__)


'''
g注入了4个属性
语言
g.language

基于请求的错误信息，主要在事务中，可以多步设定，更灵活返回报错信息
g.error_resp

g.user_id
全局用户uuid

g.access_token
需要刷新的话就赋值

g.db_commit
是否需要在after时提交
'''
e_code = 500


def init(_app: Flask):
    @_app.before_request
    def before():
        """设置语言"""
        g.language = 'zh'
        g.user_id = None
        g.access_token = None
        g.db_commit = False

    @_app.after_request
    def after(response: Response):
        # 基于请求的自动提交
        if response.status_code == 200 and g.db_commit:
            db.session.commit()
        return response

    @_app.errorhandler(Exception)
    def error(e: BaseException):
        log.exception(e)
        # 优先截胡自定义声明的error_resp
        if _e := getattr(g, 'error_resp', None):
            return resp(_e, code=-1)
        elif isinstance(e, ValidationError):
            return resp(RespMsg.params_error), getattr(e, 'code', e_code)
        elif isinstance(e, exc.IntegrityError):
            if isinstance(e.orig, pg_errors.UniqueViolation):
                return resp(RespMsg.already_exist), e_code
            return resp(RespMsg.database_error), e_code
        elif isinstance(e, AppError):
            return resp(e.msg), e_code
        if dev:
            return resp(str(e)), getattr(e, 'code', e_code)
        return resp(RespMsg.system_error), getattr(e, 'code', e_code)


def create_app() -> Flask:
    _app = Flask(__name__)
    _app.config['REDIS_URL'] = redis_uri
    _app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_POOL_SIZE'] = 100  # 连接池大小
    # _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # flask2.3被移除
    # _app.config['SQLALCHEMY_ECHO'] = True
    _app.config["JWT_SECRET_KEY"] = "yes?"  # 设置 jwt 的秘钥
    if dev:
        _app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=99999)
    else:
        # 过期时间
        _app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=JwtConfig.jwt_access_minutes)
    # 设置刷新JWT过期时间
    # 暂时的方法是后端判断时间，距离10分钟过期时候就返回一个新的token
    # _app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=JwtConfig.jwt_refresh_minutes)
    _app.json = JSONProvider(_app)

    # 注册蓝图
    from . import test, user, flag, message
    _app.register_blueprint(test.bp)
    _app.register_blueprint(user.bp)
    _app.register_blueprint(flag.bp)
    _app.register_blueprint(message.bp)
    return _app


app = create_app()

# redis
redis_cli.init_app(app)
# pg
db.init_app(app)
# jwt
JWTManager(app)
# flask
init(app)

if config.get('profile'):
    print('=============== ========== ================')
    print('=============== 性能分析开启 ================')
    print('=============== ========== ================')
    werkzeug_profile(app)

if __name__ == '__main__':
    print(app.url_map)
