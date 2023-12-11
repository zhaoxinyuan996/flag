from util.config import config


language = config['language']
allow_languages = ('zh', 'en')


class ErrorCode:
    base_error = -255


class Message:
    """
    模块+函数+信息
    """
    user_sign_up_success = {
        'zh': '注册成功',
        'en': 'sign up success'
    }
    system_error = {
        'zh': '系统错误',
        'en': 'server error'
    }

    def __getattribute__(self, item):
        return super().__getattribute__(item)[language]


for k, v in Message.__dict__.items():
    if not k.startswith('__'):
        if len(v.keys()) != len(allow_languages):
            raise RuntimeError('消息格式错误')


message = Message()
