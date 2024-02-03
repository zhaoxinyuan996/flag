from datetime import datetime
from typing import Optional, List
from uuid import UUID

from app.util import Model


class Message(Model):
    id: int
    type: int
    send_id: UUID
    receive_id: UUID
    flag_id: Optional[UUID]
    extra: Optional[str] = ''
    content: str
    create_time: datetime


class Notice(Model):
    id: Optional[int]
    version: Optional[str]
    user_class: Optional[int]
    title: Optional[str]
    content: Optional[str]
    create_time: Optional[datetime]


class AskNoticeReq(Model):
    id: int


class AskNotice(Model):
    id: int
    version: str
    title: str
    content: str
    create_time: datetime


class ReceiveMessage(Model):
    id: int
