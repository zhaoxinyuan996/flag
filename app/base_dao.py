from datetime import datetime
from functools import partial
from typing import Callable, Any, Union

from sqlalchemy import Row

from util.database import db


_ele = {int, float, str, datetime}
_builtins = {dict, list, set, int, float, str, datetime}


def build_model(t, keys, struct) -> Any:
    """
    sql返回结果结合pydantic
    :param t: 类型
    :param keys: 读数据库时候的key
    :param struct: 数据体
    """
    if type_ := getattr(t, '__origin__', None):

        if type_ in _builtins:
            assert type_ is type(struct)
        if type_ is list:
            return [build_model(t.__args__[0], keys, i) for i in struct]
        elif type_ is tuple:
            return struct[0]
        elif type_ is dict:
            return t(**struct)
        elif type_ is int or type_ is float or type_ is str:
            return struct
        elif type_ is Union:
            if type(None) in t.__args__:
                if not struct:
                    return None
                else:
                    return build_model(t.__args__[0], keys, struct)
            else:
                return build_model(t.__args__[0], keys, struct)
    if keys is None:
        return t(**struct)
    if t in _ele:
        if isinstance(struct, Row):
            return struct
        return struct[0][0]
    return t(**dict(zip(keys, struct[0] if isinstance(struct, list) else struct)))


def wrap(self, f: Callable, *args, **kwargs) -> Any:
    """装饰器，如果dao方法声明了返回值，则按照返回值格式化"""
    if ret := getattr(f, '__annotations__').get('return', None):
        resp = f(self, *args, **kwargs)
        model, entry = resp
        return build_model(ret, model, entry)
    f(self, *args, **kwargs)
    return None


class Dao:

    def __init__(self):
        for k, v in type(self).__dict__.items():
            if not k.startswith('__') and isinstance(v, Callable):
                setattr(self, k, partial(wrap, self, getattr(type(self), k)))

    @staticmethod
    def execute(sql: str, **kwargs) -> Any:
        return db.execute(sql, **kwargs)

    @staticmethod
    def location(column: str):
        return f'array[ST_x({column}), ST_y({column})] {column}'