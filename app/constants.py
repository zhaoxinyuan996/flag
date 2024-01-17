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
    # 用户信息
    user_info = 7200
    # 区域标记数
    region_flag = 1800


class InEnumMeta(EnumMeta):
    def __contains__(cls, member):
        return member in cls._value2member_map_


class InEnum(Enum, metaclass=EnumMeta):
    ...


allow_picture_type = frozenset(('jpg', 'png', 'gif', 'jpeg'))
# 用户头像限制1m
user_picture_size = 3 * 1024 * 1024
# flag图片一共大小限制10m
flag_picture_size = 10 * 1024 * 1024
# 头像，如果小于这个值，就不做缩略图
user_picture_thumbnail_size = 50 * 1024
# flag
flag_picture_thumbnail_size = 100 * 1024


class JwtConfig:
    jwt_access_minutes = 30
    jwt_refresh_minutes = 1440
    # 每次请求判断，快超时就重新发一个
    re_jwt_timestamp = 600


class FileType:
    head_pic = 'head-pic'
    flag_pic = 'flag-pic'


class StatisticsType:
    like_users_up = 'like_users_up'
    like_users_down = 'like_users_down'
    fav_users_up = 'fav_users_up'
    fav_users_down = 'fav_users_down'
    comment_users_up = 'comment_users_up'
    comment_users_down = 'comment_users_down'


class FlagNum:
    normal_user = 50
    vip_user = 200
    hidden_user = 1000


class UserClass:
    signing_out = -2
    block = -1
    normal = 0
    vip = 1
    hidden = 2


class Message(dict):
    __slots__ = ()


class RespMsg:
    """
    模块+函数+信息
    """
    user_sign_up_success = Message({
        'zh': '注册成功',
        'en': 'sign up success'
    })
    user_sign_up_username_weak = Message({
        'zh': '用户名不符合规范',
        'en': 'username does not comply with regulations'
    })
    user_sign_up_password_weak = Message({
        'zh': '密码强度不足',
        'en': 'password is too weak'
    })
    user_not_exist = Message({
        'zh': '用户不存在',
        'en': 'user not exist',
        'code': -252
    })
    cant_follow_self = Message({
        'zh': '不能关注自己',
        'en': 'cant follow self'
    })
    cant_black_self = Message({
        'zh': '不能拉黑自己',
        'en': 'cant block self'
    })
    user_sign_in_success = Message({
        'zh': '登录成功',
        'en': 'sign in success'
    })
    user_sign_in_password_error = Message({
        'zh': '密码错误',
        'en': 'password error'
    })
    user_picture_format_error = Message({
        'zh': '只支持类型：',
        'en': 'only supported pic type:'
    })
    already_exist = Message({
        'zh': '已存在',
        'en': 'already exist'
    })
    database_error = Message({
        'zh': '数据库错误',
        'en': 'database error',
        'code': -253
    })
    too_long = Message({
        'zh': '长度超限',
        'en': 'too long'
    })
    too_large = Message({
        'zh': '大小超限',
        'en': 'too large'
    })
    flag_not_exist = Message({
        'zh': '标记不存在',
        'en': 'flag not exist',
        'code': -248
    })
    flag_cant_cover_others_flag = Message({
        'zh': '不可以覆盖别人的标记哦',
        'en': 'cant cover others flag',
        'code': -249
    })
    comment_not_exist = Message({
        'zh': '评论不存在',
        'en': 'comment not exist'
    })
    in_black_list = Message({
        'zh': '在黑名单中或用户不存在',
        'en': 'in black list or user not exist'
    })
    success = Message({
        'zh': '成功',
        'en': 'success'
    })
    flag_limit = Message({
        'zh': '创建的标记已达上限',
        'en': 'created flag has reached its maximum limit',
        'code': -250
    })
    blocked_user = Message({
        'zh': '你已被锁定',
        'en': 'you have been locked',
        'code': -251
    })
    params_error = Message({
        'zh': '参数错误',
        'en': 'params error',
        'code': -254
    })
    system_error = Message({
        'zh': '系统错误',
        'en': 'server error',
        'code': -255
    })


# 防止code码重复
_codes = set()
for v in vars(RespMsg).values():
    if isinstance(v, Message) and 'code' in v:
        if v['code'] in _codes:
            raise RuntimeError(f'code码重复：{v}')
        _codes.add(v['code'])
    else:
        continue

del _codes


class AppError(Exception):
    def __init__(self, msg: Union[Message, str, None]):
        self.msg = msg


class DCSLockError(AppError):
    """分布式锁在占用"""


class UndefinedError(AppError):
    ...
