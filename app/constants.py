from enum import EnumMeta, Enum
from typing import Union


class FlagApp:
    version: tuple = (1, 0, 0)

    @property
    def text_version(self):
        return '.'.join(self.version)


flag_app = FlagApp()


class CacheTimeout:
    """缓存超时时间"""
    # jwt
    jwt = 300
    # 用户信息
    user_info = 1500
    # 区域标记数
    region_flag = 1800
    # 标记信息
    flag_info = 120
    # app点亮
    app_illuminate = 180


class InEnumMeta(EnumMeta):
    def __contains__(cls, member):
        return member in cls._value2member_map_


class InEnum(Enum, metaclass=EnumMeta):
    ...


allow_picture_type = frozenset(('jpg', 'png', 'gif', 'jpeg'))
# 用户头像限制2m
user_picture_size = 2 * 1024 * 1024
# flag单张限制3m
flag_picture_size = 3 * 1024 * 1024


class JwtConfig:
    # 半天
    jwt_access_minutes = 720
    # 暂时没用上
    jwt_refresh_minutes = 1440


class FileType:
    head_pic = 'head-pic'
    flag_pic = 'flag-pic'


class StatisticsType:
    like = 'like'
    fav = 'fav'
    comment = 'comment'


class FlagNum:
    normal_user = 50
    vip_user = 200
    senior_user = 1000


class UserClass:
    signing_out = -2
    block = -1
    normal = 0
    vip = 1
    senior = 2


class UserMessageType:
    follow = 0
    like = 1
    fav = 2
    comment = 3


class RespMessage(dict):
    __slots__ = ()


class RespMsg:
    """
    模块+函数+信息
    """
    user_sign_up_success = RespMessage({
        'zh': '注册成功',
        'en': 'sign up success'
    })
    user_sign_up_username_weak = RespMessage({
        'zh': '用户名不符合规范',
        'en': 'username does not comply with regulations'
    })
    user_sign_up_password_weak = RespMessage({
        'zh': '密码强度不足',
        'en': 'password is too weak'
    })
    user_not_exist = RespMessage({
        'zh': '用户不存在',
        'en': 'user not exist',
        'code': -252
    })
    cant_follow_self = RespMessage({
        'zh': '不能关注自己',
        'en': 'cant follow self'
    })
    cant_black_self = RespMessage({
        'zh': '不能拉黑自己',
        'en': 'cant block self'
    })
    user_sign_in_success = RespMessage({
        'zh': '登录成功',
        'en': 'sign in success'
    })
    user_sign_in_password_error = RespMessage({
        'zh': '密码错误',
        'en': 'password error'
    })
    user_picture_format_error = RespMessage({
        'zh': '只支持类型：',
        'en': 'only supported pic type:'
    })
    already_exist = RespMessage({
        'zh': '已存在',
        'en': 'already exist'
    })
    database_error = RespMessage({
        'zh': '数据库错误',
        'en': 'database error',
        'code': -253
    })
    too_long = RespMessage({
        'zh': '长度超限',
        'en': 'too long'
    })
    too_large = RespMessage({
        'zh': '大小超限',
        'en': 'too large'
    })
    id_illegal = RespMessage({
        'zh': '非法id',
        'en': 'illegal id'
    })
    flag_not_exist = RespMessage({
        'zh': '标记不存在',
        'en': 'flag not exist',
        'code': -248
    })
    flag_cant_cover_others_flag = RespMessage({
        'zh': '不可以覆盖别人的标记哦',
        'en': 'cant cover others flag',
        'code': -249
    })
    comment_not_exist = RespMessage({
        'zh': '评论不存在',
        'en': 'comment not exist'
    })
    in_black_list = RespMessage({
        'zh': '在黑名单中或用户不存在',
        'en': 'in black list or user not exist'
    })
    success = RespMessage({
        'zh': '成功',
        'en': 'success'
    })
    flag_limit = RespMessage({
        'zh': '创建的标记已达上限',
        'en': 'created flag has reached its maximum limit',
        'code': -250
    })
    blocked_user = RespMessage({
        'zh': '你已被锁定',
        'en': 'you have been locked',
        'code': -251
    })
    params_error = RespMessage({
        'zh': '参数错误',
        'en': 'params error',
        'code': -254
    })
    system_error = RespMessage({
        'zh': '系统错误',
        'en': 'server error',
        'code': -255
    })


# 防止code码重复
_codes = set()
for v in vars(RespMsg).values():
    if isinstance(v, RespMessage) and 'code' in v:
        if v['code'] in _codes:
            raise RuntimeError(f'code码重复：{v}')
        _codes.add(v['code'])
    else:
        continue

del _codes


class AppError(Exception):
    msg = None

    def __init__(self, msg: Union[RespMessage, str, None] = None):
        if msg is not None:
            self.msg = msg
        super().__init__(self.msg)


class EmojiNotSupport(AppError):
    msg = '该emoji表情暂未支持'


class DCSLockError(AppError):
    """分布式锁在占用"""


class UndefinedError(AppError):
    ...
