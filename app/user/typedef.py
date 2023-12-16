from datetime import datetime
from typing import Optional
from app.util import Model


class User(Model):
    id: Optional[int]

    nickname: Optional[str]
    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]
    sex: Optional[int]

    wechat_id: Optional[str]
    google_id: Optional[str]
    apple_id: Optional[str]

    signature: Optional[str]
    profile_picture: Optional[str]
    background_picture: Optional[str]

    create_time: Optional[datetime]
    vip_deadline: Optional[datetime]
    block_deadline: Optional[datetime]
    alive_deadline: Optional[datetime]

    belong: Optional[str]
    location_x: Optional[float]
    location_y: Optional[float]


class SignUp(User):
    username: str
    password: str
    nickname: str


class SignIn(User):
    username: str
    password: str


class UserId(User):
    id: int


class SetUserNickname(User):
    nickname: str


class SetUserSignature(User):
    signature: str


if __name__ == '__main__':
    ...
