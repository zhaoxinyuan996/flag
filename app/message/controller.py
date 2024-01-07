import os
from flask import Blueprint
from flask_jwt_extended import get_jwt_identity
from app.constants import RespMsg
from app.message.dao import dao
from app.message.typedef import SendMessage, ReceiveMessage
from app.user.controller import exists_black_list
from app.util import custom_jwt, args_parse, resp

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')


@bp.route('/send-message', methods=['post'])
@args_parse(SendMessage)
@custom_jwt()
def send_message(send: SendMessage):
    """发送消息"""
    user_id = g.user_id
    if exists_black_list(send.receive_id, user_id):
        return resp(RespMsg.in_black_list, -1)
    dao.send_message(user_id, send.receive_id, 1, send.content)
    return resp(RespMsg.success)


@bp.route('/receive-message', methods=['post'])
@args_parse(ReceiveMessage)
@custom_jwt()
def receive_message(receive: ReceiveMessage):
    """接收消息"""
    user_id = g.user_id
    all_contents = dao.receive_message(user_id, receive.id)
    return resp([contents.model_dump() for contents in all_contents])
