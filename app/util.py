"""web的一些注入解析等小功能"""
import os
import logging
import time
from datetime import datetime
from functools import wraps
from threading import Lock
from uuid import UUID
import ujson
from flask.json.provider import DefaultJSONProvider
from pydantic import BaseModel
from typing import Any, Optional, Callable, Union, Set, Dict, Tuple, List
from flask_jwt_extended import verify_jwt_in_request, create_access_token
from flask_jwt_extended.view_decorators import LocationType
from werkzeug.middleware.profiler import ProfilerMiddleware

from util.database import redis_cli
from util.wrappers import thread_lock
from .base_dao import build_model
from .constants import RespMessage, JwtConfig, DCSLockError
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
    mq_local.put(f'{user_id}|{remote_ip}')


def dcs_lock(key: str, with_user: bool = True, ex: int = 5000, raise_: bool = True):
    """
    分布式锁
    @:param key         分布式锁的key
    @:param with_user   分布式锁是否区分用户
    @:param ex          超时时间
    @:param raise_      锁被占用是否抛错
    """
    def f1(func: Callable):
        @wraps(func)
        def f2(*args, **kwargs):
            k = f'{key}-{g.user_id}' if with_user else key
            while redis_cli.set(k, nx=True, ex=ex) is None:
                # 抛错
                if raise_:
                    raise DCSLockError('操作过快')
                # 等待
                else:
                    time.sleep(0.1)
                    continue
            try:
                return func(*args, **kwargs)
            finally:
                redis_cli.delete(k)
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
    if g.access_token:
        kwargs['access_token'] = g.access_token

    if isinstance(msg, RespMessage):
        _msg = msg[g.language]
        code = msg.get('code', code)
        return jsonify({'msg': _msg, 'code': code, **kwargs})

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
        raise TypeError(f'illegal type: {obj}')

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return ujson.dumps(obj, default=self.default)

    def loads(self, s: Union[str, bytes], **kwargs: Any) -> Any:
        return ujson.loads(s)

    def response(self, obj: Any) -> Response:
        return self._app.response_class(self.dumps(obj))


class StatisticsType:
    like = 'like'
    fav = 'fav'
    comment = 'comment'


class StatisticsUtil:
    lock = Lock()
    sync_keys = (StatisticsType.fav, StatisticsType.comment)
    _async_keys = (StatisticsType.like, )

    def __init__(self):
        self.statistics_cache: Dict[UUID, Dict[str, Tuple[Set[UUID], Set[UUID]]]] = {}

    def add(self, user_id: UUID, flag_id: UUID, key: str, num: int):
        # num是0则删除，num是1则新增
        # 嵌套了好几层，就不用default dict了
        if flag_id not in self.statistics_cache:
            self.statistics_cache[flag_id] = {}
        if key not in self.statistics_cache[flag_id]:
            self.statistics_cache[flag_id][key] = (set(), set())
        self.statistics_cache[flag_id][key][num].add(user_id)

    def build_flag_statistics_sql(self) -> List[str]:
        all_sql = []
        for flag_id, kv in self.statistics_cache.items():
            loop = []
            for key, tuples in kv.items():
                # 剔除共有的user_id
                del_users, add_users = tuples
                del_users: Set[UUID] = del_users.difference(add_users)
                add_users: Set[UUID] = add_users.difference(del_users)
                if key == StatisticsType.like and del_users:
                    loop.extend((f"{key}_users = delete({key}_users, '{uuid}')" for uuid in del_users))
                if key == StatisticsType.like and add_users:
                    loop.extend((f"{key}_users ['{uuid}']=null" for uuid in add_users))
                num_diff = len(add_users) - len(del_users)
                if num_diff:
                    loop.append(f"{key}_num={key}_num+{num_diff} ")
            if loop:
                all_sql.append(f"update flag_statistics set {','.join(loop)}, "
                               f"update_time=current_timestamp where flag_id='{flag_id}'")
        self.statistics_cache.clear()
        return all_sql

    @thread_lock(lock)
    def auto_exec(self, user_id: UUID, flag_id: UUID, key: str, num: int):
        """同步接口保证事务一致性"""
        self.add(user_id, flag_id, key, num)
        return ';'.join(self.build_flag_statistics_sql())


class UserMessage:
    __slots__ = ('send_id', 'receive_id', 'flag_id', 'type_', 'content', 'extra')

    def __init__(self, send_id: UUID, receive_id: UUID, flag_id: Optional[UUID], type_: int, content: str, extra: str):
        self.send_id = send_id
        self.receive_id = receive_id
        self.flag_id = flag_id
        self.type_ = type_
        self.content = content
        self.extra = extra

    def __hash__(self):
        return hash(f'{self.send_id}{self.receive_id}{self.flag_id}{self.content}')


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
