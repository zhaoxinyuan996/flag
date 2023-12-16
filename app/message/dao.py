from typing import Tuple, Optional, List

from app.message.typedef import ReceiveMessageResp
from util.database import Dao


class MessageDao(Dao):
    def send_message(self, send_id: int, receive_id: int, type_: int, content: str):
        sql = ('insert into message (type, send_id, receive_id, content, create_time) '
               'values(:type_, :send_id, :receive_id, :content, current_timestamp)')
        self.execute(sql, send_id=send_id, receive_id=receive_id, type_=type_, content=content)

    def receive_message(self, user_id: int, last_message_id: int) -> List[ReceiveMessageResp]:
        sql = ('with s as ('
               "select max(id) max_id, type, send_id, "
               "json_agg((json_build_object('content', content, 'create_time', create_time))) obj "
               "from message m where receive_id=:user_id and id>:last_message_id group by type, send_id) "
               "select max(max_id) max_id, type, json_agg(json_build_object('send_id', send_id, 'contents', obj)) "
               "contents from s group by type")
        return self.execute(sql, user_id=user_id, last_message_id=last_message_id)


dao = MessageDao()
