from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import constr, conint
from app.constants import UserClass, FlagNum, UndefinedError
from app.util import Model


_NICKNAME = constr(max_length=20)
_SIGNATURE = constr(max_length=50)


class User(Model):
    id: UUID

    nickname: _NICKNAME
    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]
    is_man: Optional[int]
    signature: Optional[_SIGNATURE]
    avatar_name: Optional[str]
    bg_avatar_name: Optional[str]
    flag_num: int
    create_time: datetime
    vip_deadline: Optional[datetime]
    block_deadline: Optional[datetime]
    alive_deadline: Optional[datetime]

    belong: Optional[str]
    local: Optional[str]
    hidden: bool

    @property
    def user_class(self) -> int:
        if self.block_deadline and self.block_deadline > datetime.now():
            return UserClass.block
        elif self.hidden is True:
            return UserClass.hidden
        elif self.vip_deadline and self.vip_deadline > datetime.now():
            return UserClass.vip
        else:
            return UserClass.normal

    @property
    def allow_flag_num(self) -> int:
        if self.user_class == UserClass.block:
            return 0
        elif self.user_class == UserClass.normal:
            return FlagNum.normal_user - self.flag_num
        elif self.user_class == UserClass.vip:
            return FlagNum.vip_user - self.flag_num
        elif self.user_class == UserClass.hidden:
            return FlagNum.hidden_user - self.flag_num
        raise UndefinedError('user class')


class QueryUser(Model):
    id: Optional[UUID]


class OverviewUser(Model):
    id: UUID
    nickname: _NICKNAME
    is_man: Optional[int]
    flag_num: int

    signature: _SIGNATURE
    avatar_name: str

    vip_deadline: datetime
    block_deadline: datetime


class OtherUser(Model):
    id: UUID
    nickname: _NICKNAME
    is_man: Optional[int]
    flag_num: int

    signature: _SIGNATURE
    avatar_name: str

    vip_deadline: datetime
    block_deadline: datetime

    is_follow: int
    is_black: int


class SignUp(User):
    username: str
    password: str


class SignWechat(Model):
    code: str


class SignIn(User):
    username: str
    password: str


class UserId(Model):
    id: UUID


class SetUserinfo(Model):
    nickname: Optional[_NICKNAME]
    is_man: Optional[bool]
    phone: Optional[conint(lt=19999999999)]
    signature: Optional[_SIGNATURE]


if __name__ == '__main__':
    ...
