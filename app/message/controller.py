import os
import pickle
from uuid import UUID

from flask import Blueprint, g
from app.message.dao import dao
from app.message.typedef import AskNoticeReq, ReceiveMessage
from app.util import custom_jwt, args_parse, resp, UserMessage
from util.msg_middleware import mq_user_msg

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')


def push_message(send_id: UUID, receive_id: UUID,
                 type_: int, content: str = None, flag_id: UUID = None, extra: str = ''):
    mq_user_msg.put(pickle.dumps(UserMessage(send_id, receive_id, flag_id, type_, content, extra)))


@bp.route('/ask-notice', methods=['post'])
@args_parse(AskNoticeReq)
@custom_jwt()
def ask_notice(ask: AskNoticeReq):
    from app.user.controller import get_user_info
    return resp([n.model_dump() for n in dao.ask_notice(ask.id, get_user_info().user_class)])


@bp.route('/receive-message', methods=['post'])
@args_parse(ReceiveMessage)
@custom_jwt()
def receive_message(receive: ReceiveMessage):
    """接收消息"""
    user_id = g.user_id
    all_contents = dao.receive_message(user_id, receive.id)
    return resp([contents.model_dump() for contents in all_contents])
