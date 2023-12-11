from flask import Flask
from util.config import uri
from util.database import db
from .util import init
from . import test, user


def create_app() -> Flask:
    _app = Flask(__name__)
    _app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_POOL_SIZE'] = 100  # 连接池大小
    # _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 事务自动提交
    # _app.config['SQLALCHEMY_ECHO'] = True
    return _app


app = create_app()
# 注册蓝图
app.register_blueprint(test.bp)
app.register_blueprint(user.bp)
db.init_app(app)
init(app)


if __name__ == '__main__':
    print(app.url_map)
