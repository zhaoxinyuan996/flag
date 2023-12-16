from enum import EnumMeta, Enum


class InEnumMeta(EnumMeta):
    def __contains__(cls, member):
        return member in cls._value2member_map_


class InEnum(Enum, metaclass=EnumMeta):
    ...


allow_picture_type = ('jpg', 'png', 'gif')
# 用户头像限制1m
user_picture_size = 1024 * 1024
# flag图片一共大小限制10m
flag_picture_size = 10 * 1024 * 1024
# 头像，如果小于这个值，就不做缩略图
user_picture_thumbnail_size = 50 * 1024
# flag
flag_picture_thumbnail_size = 100 * 1024


class FileType(InEnum):
    head_pic = 'head-pic'
    flag_pic = 'flag-pic'


class UserLevel(InEnum):
    signing_out = -2
    block = -1
    normal = 0
    vip = 1


class FlagType(InEnum):
    init = 0  # 初始


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
    user_sign_in_not_exist = Message({
        'zh': '用户不存在',
        'en': 'user not exist'
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
        'en': 'flag not exist'
    })
    in_black_list = Message({
        'zh': '在黑名单中或用户不存在',
        'en': 'in black list or user not exist'
    })
    success = Message({
        'zh': '成功',
        'en': 'success'
    })
    blocked_user = Message({
        'zh': '你已被锁定',
        'en': 'you have been locked'
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
