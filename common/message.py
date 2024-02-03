from threading import Lock
from typing import Set
from app.message.dao import dao
from app.util import UserMessage
from common.app_shadow import placeholder_app
from util import db
from util.msg_middleware import mq_user_msg
from util.wrappers import thread_lock


class UserMsgHandler:
    lock = Lock()

    def __init__(self):
        self.filter: Set[UserMessage] = set()

    @thread_lock(lock)
    def add(self, msg: UserMessage):
        self.filter.add(msg)

    @thread_lock(lock)
    def flush(self):
        with placeholder_app.app_context():
            while self.filter:
                msg = self.filter.pop()
                dao.send_message(msg.type_, msg.send_id, msg.receive_id, msg.flag_id, msg.extra, msg.content)
            db.session.commit()


user_msg_handler = UserMsgHandler()
mq_user_msg.register_cb(user_msg_handler.add)
