from datetime import datetime
from typing import Optional
from pydantic import constr
from app.typedef import UUID, LOCATION
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
    profile_picture: Optional[str]
    background_picture: Optional[str]

    create_time: Optional[datetime]
    vip_deadline: Optional[datetime]
    block_deadline: Optional[datetime]
    alive_deadline: Optional[datetime]

    belong: Optional[str]
    location: Optional[LOCATION]


class SignUp(User):
    username: str
    password: str
    nickname: _NICKNAME


class SignWechat(Model):
    code: str
    nickname: _NICKNAME
    profile_picture: str


class SignIn(User):
    username: str
    password: str


class UserId(User):
    id: UUID


class SetUserNickname(User):
    nickname: _NICKNAME


class SetUserSignature(User):
    signature: _SIGNATURE


if __name__ == '__main__':
    ...
