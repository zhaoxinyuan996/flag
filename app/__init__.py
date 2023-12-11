from flask import Flask
from util.config import uri
from util.database import db
from . import test


def create_app() -> Flask:
    _app = Flask(__name__)
    _app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['SQLALCHEMY_POOL_SIZE'] = 100  # 连接池大小
    _app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # 事务自动提交
    # _app.config['SQLALCHEMY_ECHO'] = True
    return _app





app = create_app()
app.register_blueprint(test.bp)

db.init_app(app)
print(app.url_map)


if __name__ == '__main__':
    print(app.url_map)
