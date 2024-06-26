from typing import List, Optional
from uuid import UUID

from app.base_dao import Dao
from app.message.typedef import AskNotice, Message


class MessageDao(Dao):
    expires = '-7days'

    def ask_notice(self, notice_id: int, user_class: int) -> List[AskNotice]:
        sql = ('select id, version, title, content, create_time from notice '
               'where id>:id and user_class<=:user_class order by id desc')
        return self.execute(sql, id=notice_id, user_class=user_class)

    def send_message(self, type_: int, send_id: UUID, receive_id: UUID, flag_id: UUID,
                     extra: Optional[str], content: str):
        sql = ('insert into message (type, send_id, receive_id, flag_id, extra, content, create_time) '
               'values(:type_, :send_id, :receive_id, :flag_id, :extra, :content, current_timestamp)')
        self.execute(sql, send_id=send_id, receive_id=receive_id, flag_id=flag_id,
                     extra=extra, type_=type_, content=content)

    def latest_message_id(self, user_id: UUID) -> Optional[int]:
        sql = 'select max(id) id from message where receive_id=:user_id and create_time>current_timestamp + :expires'
        return self.execute(sql, user_id=user_id, expires=self.expires)

    def receive_message(self, user_id: UUID,  id_: int) -> List[Message]:
        sql = ('with s1 as (update message set read=true where receive_id=:user_id and id>:id and '
               '(not read or create_time>current_timestamp + :expires) returning *)'
               'select * from s1 order by id desc')
        return self.execute(sql, id=id_, user_id=user_id, expires=self.expires)

    def clean_timeout_message(self):
        sql = 'delete from message where read and create_time<current_timestamp + :expires'
        self.execute(sql, expires=self.expires)


dao: MessageDao = MessageDao()
