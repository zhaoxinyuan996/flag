import logging

from flask import g
from flask_redis import FlaskRedis
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine.result import RMKeyView
from typing import Tuple, Any, Optional
from contextlib import contextmanager
from util.config import config
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


log = logging.getLogger(__name__)


class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
            g.db_commit = False
        except Exception as e:
            self.session.rollback()
            raise e

    def execute(self, sql: str, **kwargs) -> Optional[Tuple[RMKeyView, Any]]:
        g.db_commit = True
        log.info(text(sql))
        response = self.session.execute(text(sql), kwargs)
        if response.returns_rows:
            records = response.fetchall()
            log.info(str(records))
            return response.keys(), records
        return None


redis_cli = FlaskRedis()


db = SQLAlchemy()


if __name__ == '__main__':
    from typing import *

    class Test(BaseModel):
        f1: int
        f2: str
        f3: List[int]
        f4: List[str]
        f5: dict

    from app import app
    with app.app_context():

        insert = '''insert into test values(1,'2', array[1,2,3], array['2', '3', '4'], '{"test": 123}')'''
        delete = 'delete from 1test'
        select = 'select * from test'
        print(config)

        res = db.execute(select)
        print(res)
