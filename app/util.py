"""web的一些注入解析等小功能"""
import logging

from app.constants import message, ErrorCode
from util.config import config
from util.database import build_model
from flask import request, Flask, Response, jsonify


log = logging.getLogger(__name__)


def resp(data: str, code: int = 0, **kwargs):
    return jsonify({'data': data, 'code': code, **kwargs})


def parse(model):
    return build_model(model, None, request.json)


def init(app: Flask):
    @app.before_request
    def before():
        ...

    @app.after_request
    def after(response: Response):
        return response

    @app.errorhandler(Exception)
    def error(e: BaseException):
        log.exception(e)
        if config['env'] == 'dev':
            return resp(f'{e}', ErrorCode.base_error), getattr(e, 'code', 500)
        else:
            return resp(message.system_error, ErrorCode.base_error), getattr(e, 'code', 500)
