"""web的一些注入解析等小功能"""
import logging
import random
from datetime import datetime
from functools import wraps, partial
from uuid import UUID

import requests
from pydantic import BaseModel
from typing import Any, Optional, Callable, Union, Set, Dict
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import verify_jwt_in_request, get_jwt, create_access_token
from flask_jwt_extended.view_decorators import LocationType
from pydantic_core import PydanticUndefined
from common.job import DelayJob
from util.database import db, redis_cli
from .base_dao import build_model, base_dao
from .constants import Message, JwtConfig, DCSLockError
from util.config import dev
from flask import request, jsonify, current_app, g


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


def _refresh_user(user_id: UUID, ip: str):
    """获取ip位置"""
    from app import app

    def _get_local():
        try:
            data = requests.get(api + ip).json()
            log.info(str(data))
            return data[key]
        except requests.RequestException:
            return None

    if ip == '127.0.0.1':
        return

    apis = (
        ('http://ip.360.cn/IPQuery/ipquery?ip=', 'data'),
        ('http://www.ip508.com/ip?q=', 'addr'),
        ('http://whois.pconline.com.cn/ipJson.jsp?json=true&ip=', 'addr'),
    )
    idx_list = [i for i in range(len(apis))]
    random.shuffle(idx_list)
    local = ''
    for i in idx_list:
        api, key = apis[i]
        local = _get_local()
        if local:
            break
    with app.app_context():
        base_dao.refresh(user_id, local=local)
        db.session.commit()


def refresh_user(user_id: UUID):
    """刷新用户的最后活跃时间和网络ip的解析地址"""
    remote_ip = request.headers.get('X-Forwarded-For', '').split(',')[0] or request.remote_addr
    return partial(_refresh_user, user_id, remote_ip)


def dcs_lock(key: str, ex=5000):
    """分布式锁"""
    def f1(func: Callable):
        @wraps(func)
        def f2(*args, **kwargs):
            k = f'{key}-{g.user_id}'
            # 锁被占用
            if redis_cli.get(k):
                raise DCSLockError('操作过快')
            try:
                redis_cli.set(k, ex=ex)
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
            verify_jwt_in_request(optional, fresh, refresh, locations, verify_type, skip_revocation_check)

            jwt_info = get_jwt()
            user_id: UUID = UUID(jwt_info['sub'])
            g.user_id = user_id
            if datetime.timestamp(datetime.now()) + JwtConfig.re_jwt_timestamp > jwt_info['exp']:
                # 添加ip的时候启动这个
                DelayJob.job_queue.put(refresh_user(user_id))
                g.access_token = create_access_token(identity=user_id)

            return current_app.ensure_sync(fn)(*args, **kwargs)

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


class JSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, BaseModel):
            return obj.model_dump_json()

        return super().default(obj)


class Model(BaseModel):
    def __init__(self, **kwargs):
        cls = type(self)
        kw = {}
        for cls in cls.__mro__[:-3]:
            kw.update({k: None for k in cls.__annotations__ if cls.model_fields[k].default is PydanticUndefined})
        kw.update(kwargs)
        # [kw.pop(i) for i in args if kw[i] is None]
        super().__init__(**kw)

    def check(self, *args):
        for a in args:
            assert getattr(self, a)
