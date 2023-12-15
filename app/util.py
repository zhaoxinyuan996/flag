"""web的一些注入解析等小功能"""
import logging
from enum import Enum, EnumMeta
from datetime import datetime
from functools import wraps
from typing import Any, Optional, Literal
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.view_decorators import LocationType
from pydantic import BaseModel

from util.config import dev
from util.database import build_model
from flask import request, jsonify, current_app

log = logging.getLogger(__name__)


def custom_jwt(
        optional: bool = False,
        fresh: bool = False,
        refresh: bool = False,
        locations: Optional[LocationType] = None,
        verify_type: bool = True,
        skip_revocation_check: bool = False,
) -> Any:
    """重写jwt_required，dev环境下不开启dev"""
    if optional is None:
        optional = dev

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(
                optional, fresh, refresh, locations, verify_type, skip_revocation_check
            )
            return current_app.ensure_sync(fn)(*args, **kwargs)

        return decorator

    return wrapper


def resp(msg: Any, code: int = 0, **kwargs):
    return jsonify({'msg': msg, 'code': code, **kwargs})


def args_parse(model):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            param = build_model(model, None, request.json)
            return fn(param, *args, **kwargs)
            # return current_app.ensure_sync(fn)(param, *args, **kwargs)

        return decorator

    return wrapper


def get_request_list(body) -> dict:
    """同名的参数key用这个按照原样取出来"""
    d = {}
    for k in body.keys():
        lis = body.getlist(k)
        d[k] = lis if len(lis) > 1 else lis[0]
    return d


class JSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        return super().default(obj)


class Model(BaseModel):
    def __init__(self, **kwargs):
        cls = type(self)
        kw = {}
        for cls in cls.__mro__[:-3]:
            kw.update({k: None for k in cls.__annotations__})
        kw.update(kwargs)
        # [kw.pop(i) for i in args if kw[i] is None]
        super().__init__(**kw)

    def check(self, *args):
        for a in args:
            assert getattr(self, a)


class InEnumMeta(EnumMeta):
    def __contains__(cls, member):
        return member in cls._value2member_map_


class InEnum(Enum, metaclass=EnumMeta):
    ...
