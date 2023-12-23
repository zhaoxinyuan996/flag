from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import constr, conint
from app.base_typedef import LOCATION, URL
from app.util import Model


_NICKNAME = constr(max_length=10)
_SIGNATURE = constr(max_length=50)


class User(Model):
    id: Optional[UUID]

    nickname: Optional[_NICKNAME]
    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]
    sex: Optional[int]

    wechat_id: Optional[str]
    google_id: Optional[str]
    apple_id: Optional[str]

    signature: Optional[_SIGNATURE]
    avatar_url: Optional[str]

    create_time: Optional[datetime]
    vip_deadline: Optional[datetime]
    block_deadline: Optional[datetime]
    alive_deadline: Optional[datetime]

    belong: Optional[str]
    location: Optional[LOCATION]


class SignUp(User):
    username: str
    password: str


class SignWechat(Model):
    code: str


class SignIn(User):
    username: str
    password: str


class UserId(User):
    id: UUID


class SetUserinfo(Model):
    nickname: Optional[_NICKNAME]
    is_man: Optional[bool]
    phone: Optional[conint(lt=19999999999)]
    signature: Optional[_SIGNATURE]
    avatar_url: Optional[URL]


if __name__ == '__main__':
    ...
