import os

from flask import g

allow_picture_type = ('jpg', 'png', 'gif')
user_picture_size = 1048576
flag_picture_size = 10485760

_static_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'static'))
user_picture_folder = os.path.join(_static_folder, 'user_picture')
flag_picture_folder = os.path.join(_static_folder, 'flag_picture')


class ErrorCode:
    base_error = -255


class UserLevel:
    violation = -1
    normal = 0
    vip = 1


class Message:
    """
    模块+函数+信息
    """
    user_sign_up_success = {
        'zh': '注册成功',
        'en': 'sign up success'
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
