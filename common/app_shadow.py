from flask import Flask

from util import db
from util.config import db_uri

# 占位app
placeholder_app = Flask(__name__)
placeholder_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

db.init_app(placeholder_app)
