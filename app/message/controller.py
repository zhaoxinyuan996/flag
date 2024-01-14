import os
from functools import partial
from uuid import UUID

from flask import Blueprint
from app.message.dao import dao
from app.message.typedef import AskNoticeReq
from app.user.controller import get_user_info
from app.util import custom_jwt, args_parse, resp
from util.database import db

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')


def _push_message(user_id: UUID, msg: str):
    from app import app

    with app.app_context():
        db.session.commit()


def push_message(user_id: UUID, msg: str):
    """写一条消息到库里"""
    return partial(_push_message, user_id, msg)


@bp.route('/ask-notice', methods=['post'])
@args_parse(AskNoticeReq)
@custom_jwt()
def ask_notice(ask: AskNoticeReq):
    return resp([n.model_dump() for n in dao.ask_notice(ask.id, get_user_info().user_class)])


# @bp.route('/send-message', methods=['post'])
# @args_parse(SendMessage)
# @custom_jwt()
# def send_message(send: SendMessage):
#     """发送消息"""
#     user_id = g.user_id
#     if exists_black_list(send.receive_id, user_id):
#         return resp(RespMsg.in_black_list, -1)
#     dao.send_message(user_id, send.receive_id, 1, send.content)
#     return resp(RespMsg.success)
#
#
# @bp.route('/receive-message', methods=['post'])
# @args_parse(ReceiveMessage)
# @custom_jwt()
# def receive_message(receive: ReceiveMessage):
#     """接收消息"""
#     user_id = g.user_id
#     all_contents = dao.receive_message(user_id, receive.id)
#     return resp([contents.model_dump() for contents in all_contents])
