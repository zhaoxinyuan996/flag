from flask import g
from app.util import InEnum

allow_picture_type = ('jpg', 'png', 'gif')
# 用户头像限制1m
user_picture_size = 1024 * 1024
# flag图片单张大小限制5m
flag_picture_size = 5 * 1024 * 1024
# 头像，如果小于这个值，就不做缩略图
user_picture_thumbnail_size = 50 * 1024
# flag
flag_picture_thumbnail_size = 100 * 1024


class ErrorCode:
    base_error = -255


class FileType(InEnum):
    head_pic = 'head-pic'
    flag_pic = 'flag-pic'


class UserLevel(InEnum):
    block = -1
    normal = 0
    vip = 1


class FlagType(InEnum):
    init = 0  # 初始


class Message:
    """
    模块+函数+信息
    """
    user_sign_up_success = {
        'zh': '注册成功',
        'en': 'sign up success'
    }
    user_sign_up_username_weak = {
        'zh': '用户名不符合规范',
        'en': 'username does not comply with regulations'
    }
    user_sign_up_password_weak = {
        'zh': '密码强度不足',
        'en': 'password is too weak'
    }
    user_sign_up_already_exist = {
        'zh': '用户已存在',
        'en': 'user already exist'
    }
    user_sign_in_not_exist = {
        'zh': '用户不存在',
        'en': 'user not exist'
    }
    user_sign_in_success = {
        'zh': '登录成功',
        'en': 'sign in success'
    }
    user_sign_in_password_error = {
        'zh': '密码错误',
        'en': 'password error'
    }
    user_picture_format_error = {
        'zh': '只支持类型：',
        'en': 'only supported pic type:'
    }
    too_long = {
        'zh': '长度超限',
        'en': 'too long'
    }
    too_large = {
        'zh': '大小超限',
        'en': 'too large'
    }
    success = {
        'zh': '成功',
        'en': 'success'
    }
    blocked_user = {
        'zh': '你已被锁定',
        'en': 'you have been locked'
    }
    system_error = {
        'zh': '系统错误',
        'en': 'server error'
    }

    def __getattribute__(self, item) -> str:
        return super().__getattribute__(item)[g.language]


message = Message()
