"""web的一些注入解析等小功能"""
import os
import logging
import platform
import time
from datetime import datetime
from functools import wraps
from threading import Lock
from uuid import UUID
import ujson
from flask.json.provider import DefaultJSONProvider
from pydantic import BaseModel
from typing import Any, Optional, Callable, Union, Set, Dict
from flask_jwt_extended import verify_jwt_in_request, create_access_token
from flask_jwt_extended.view_decorators import LocationType
from werkzeug.middleware.profiler import ProfilerMiddleware
from util.database import redis_cli
from .base_dao import build_model
from .constants import Message, JwtConfig, DCSLockError
from util.config import dev
from flask import request, jsonify, g, Response

log = logging.getLogger(__name__)


class PictureStorage:
    __slots__ = ('filename', 'data', 'suffix')

    def __init__(self, filename: str, data: Union[str, bytes]):
        self.filename = filename
        self.suffix = self.filename.rsplit('.', 1)[-1]
        self.data = data


class PictureStorageSet:
    __slots__ = ('__set', '__mapping')

    def __init__(self, set_: Set[PictureStorage]):
        self.__set: Set[PictureStorage] = set_
        self.__mapping: Dict[str, PictureStorage] = {i.filename: i for i in set_}

    def __contains__(self, filename: str):
        if filename in self.__mapping:
            return True
        else:
            return False

    def pop(self, filename: str):
        """没设锁，这玩意应该不会竞争"""
        v = self.__mapping.pop(filename)
        self.__set.remove(v)
        return v


def refresh_user(user_id: UUID):
    """刷新用户的最后活跃时间和网络ip的解析地址"""
    remote_ip = request.headers.get('X-Forwarded-For', '').split(',')[0] or request.remote_addr
    if remote_ip == '127.0.0.1':
        return
    from util.msg_middleware import mq_local
    mq_local.put(user_id, remote_ip)


if platform.system().lower() != 'windows':
    import uwsgi


class ApiLock:
    def __init__(self, func_name: str):
        self.func_name = func_name

    if platform.system().lower() == 'windows':
        _lock_mapping = {
            'set-statistics': Lock(),
            'upload-avatar': Lock()
        }

        def __enter__(self):
            self._lock_mapping[self.func_name].acquire()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._lock_mapping[self.func_name].release()

    else:

        _lock_mapping = {
            'set-statistics': 1,
            'upload-avatar': 2
        }

        def __enter__(self):
            uwsgi.lock(self._lock_mapping[self.func_name])

        def __exit__(self, exc_type, exc_val, exc_tb):
            uwsgi.unlock(self._lock_mapping[self.func_name])


def api_lock(lock):
    """uwsgi锁"""
    def f1(func: Callable):
        @wraps(func)
        def f2(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return f2
    return f1


def custom_jwt(
        optional: bool = False,
        fresh: bool = False,
        refresh: bool = False,
        locations: Optional[LocationType] = None,
        verify_type: bool = True,
        skip_revocation_check: bool = False,
) -> Any:
    """重写jwt_required，dev环境下不开启dev"""
    if dev:
        optional = False

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 服务器每个校验2.5ms
            jwt_info = verify_jwt_in_request(optional, fresh, refresh, locations, verify_type, skip_revocation_check)[1]

            # jwt做缓存
            # encode_jwt: str = request.headers.get('Authorization', '').rsplit(' ')[-1]
            # jwt_key = f'jwt-{encode_jwt}'
            # jwt_info = redis_cli.get(jwt_key)
            # if jwt_info is None:
            #     jwt_info = verify_jwt_in_request(
            #         optional, fresh, refresh, locations, verify_type, skip_revocation_check)[1]
            #     redis_cli.set(jwt_key, pickle.dumps(jwt_info), ex=CacheTimeout.jwt)
            # else:
            #     jwt_info = pickle.loads(jwt_info)

            user_id: UUID = UUID(jwt_info['sub'])
            g.user_id = user_id
            # jwt的超时时间的一半，重新颁发jwt和记录alive时间
            if datetime.timestamp(datetime.now()) + (JwtConfig.jwt_access_minutes / 2) > jwt_info['exp']:
                # 添加ip的时候启动这个
                refresh_user(user_id)
                g.access_token = create_access_token(identity=user_id)

            return fn(*args, **kwargs)
            # return current_app.ensure_sync(fn)(*args, **kwargs)
        return decorator
    return wrapper


def resp(msg: Any, code: int = 0, **kwargs):
    if isinstance(msg, Message):
        _msg = msg[g.language]
        code = msg.get('code', code)
        return jsonify({'msg': _msg, 'code': code, **kwargs})

    if g.access_token:
        return jsonify({'msg': msg, 'code': code, 'access_token': g.access_token, **kwargs})

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


# class JSONProvider(DefaultJSONProvider):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.strftime('%Y-%m-%d %H:%M:%S')
#         elif isinstance(obj, BaseModel):
#             return obj.model_dump_json()
#
#         return super().default(obj)


class JSONProvider(DefaultJSONProvider):
    """用ujson重写"""

    @staticmethod
    def default(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, UUID):
            return str(obj)
        raise TypeError('ignore type')

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return ujson.dumps(obj, default=self.default)

    def loads(self, s: Union[str, bytes], **kwargs: Any) -> Any:
        return ujson.loads(s)

    def response(self, obj: Any) -> Response:
        return self._app.response_class(self.dumps(obj))


class Model(BaseModel):
    """为了规范还是用回原来的方法"""
    # def __init__(self, **kwargs):
    #     cls = type(self)
    #     kw = {}
    #     for cls in cls.__mro__[:-3]:
    #         kw.update({k: None for k in cls.__annotations__ if cls.model_fields[k].default is PydanticUndefined})
    #     kw.update(kwargs)
    #     # [kw.pop(i) for i in args if kw[i] is None]
    #     super().__init__(**kw)
    #
    # def check(self, *args):
    #     for a in args:
    #         assert getattr(self, a)


def werkzeug_profile(app):
    app.wsgi_app = ProfilerMiddleware(
        app.wsgi_app,
        profile_dir=os.path.join(os.path.dirname(__file__), os.pardir, 'test', 'output'),
        filename_format="{time:.0f}-{method}-{path}-{elapsed:.0f}ms.prof")
