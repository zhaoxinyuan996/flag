from typing import List, Optional
from uuid import UUID

from app.base_dao import Dao
from app.message.typedef import AskNotice


class MessageDao(Dao):
    def ask_notice(self, notice_id: int, user_class: int) -> List[AskNotice]:
        sql = ('select id, version, title, content, create_time from notice '
               'where id>:id and user_class<=:user_class order by id')
        return self.execute(sql, id=notice_id, user_class=user_class)

    def send_message(self, type_: int, send_id: UUID, receive_id: UUID, flag_id: UUID,
                     extra: Optional[str], content: str):
        sql = ('insert into message (type, send_id, receive_id, flag_id, extra, content, create_time) '
               'values(:type_, :send_id, :receive_id, :flag_id, :extra, :content, current_timestamp)')
        self.execute(sql, send_id=send_id, receive_id=receive_id, flag_id=flag_id,
                     extra=extra, type_=type_, content=content)


dao: MessageDao = MessageDao()
